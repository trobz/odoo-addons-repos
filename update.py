#!/usr/bin/env python3
"""Fetch OCA repos and generate TOML files tracking which versions each repo supports."""

import os
import requests

VERSIONS = ["12.0", "13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"]

# Non-OCA orgs: org -> explicit list of repos to track
EXTRA_ORGS = {
    "camptocamp": ["odoo-cloud-platform"],
    "forgeflow": ["stock-rma"],
}

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}


def paginate(url, params=None):
    params = dict(params or {})
    params["per_page"] = 100
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        items = resp.json()
        yield from items
        if len(items) < 100:
            break
        page += 1


def get_oca_repos():
    repos = []
    for repo in paginate("https://api.github.com/orgs/OCA/repos", {"type": "all"}):
        name = repo["name"]
        if name in ("OCB", "OpenUpgrade"):
            continue
        if name.startswith("l10n-") and name != "l10n-france":
            continue
        repos.append(name)
    return repos


def get_repo_branches(org, repo_name):
    branches = set()
    try:
        for branch in paginate(f"https://api.github.com/repos/{org}/{repo_name}/branches"):
            branches.add(branch["name"])
    except requests.HTTPError as e:
        print(f"Warning: could not fetch branches for {org}/{repo_name}: {e}")
    return branches


def write_toml_org_section(f, org, repo_versions, all_versions=False):
    """Write the [org] section of the oca/extra org list."""
    f.write(f"{org} = [\n")
    f.write("  # addons repositories\n")
    for repo in sorted(repo_versions):
        versions = repo_versions[repo]
        if not versions:
            continue
        if all_versions and versions == VERSIONS:
            f.write(f'  "{repo}",\n')
        elif all_versions:
            v_str = ", ".join(f'"{v}"' for v in versions)
            f.write(f'  ["{repo}", [{v_str}]],\n')
        else:
            f.write(f'  "{repo}",\n')
    f.write("]\n")


def main():
    # Fetch OCA repos
    print("Fetching OCA repos...")
    oca_repos = get_oca_repos()
    print(f"Found {len(oca_repos)} OCA repos")

    # org -> repo -> [versions]
    org_repo_versions = {"oca": {}}

    for i, repo in enumerate(sorted(oca_repos), 1):
        print(f"[{i}/{len(oca_repos)}] OCA/{repo}...")
        branches = get_repo_branches("OCA", repo)
        org_repo_versions["oca"][repo] = [v for v in VERSIONS if v in branches]

    # Fetch extra org repos
    for org, repos in EXTRA_ORGS.items():
        org_repo_versions[org] = {}
        for repo in repos:
            print(f"Checking {org}/{repo}...")
            branches = get_repo_branches(org, repo)
            org_repo_versions[org][repo] = [v for v in VERSIONS if v in branches]

    # Build version -> {org -> [repos]} mapping
    version_org_repos = {v: {org: [] for org in org_repo_versions} for v in VERSIONS}
    for org, repo_versions in org_repo_versions.items():
        for repo, versions in repo_versions.items():
            for v in versions:
                version_org_repos[v][org].append(repo)

    # Write per-version TOML files
    for version in VERSIONS:
        filename = f"all_repos_{version}.toml"
        with open(filename, "w") as f:
            f.write(f'versions = ["{version}"]\n')
            f.write("\n")
            f.write("[repos]\n")
            f.write('odoo = ["odoo"]\n')
            for org in org_repo_versions:
                repos_for_version = sorted(version_org_repos[version][org])
                f.write(f"{org} = [\n")
                f.write("  # addons repositories\n")
                for repo in repos_for_version:
                    f.write(f'  "{repo}",\n')
                f.write("]\n")
        total = sum(len(v) for v in version_org_repos[version].values())
        print(f"Wrote {filename} ({total} repos)")

    # Write aggregate TOML file
    versions_str = ", ".join(f'"{v}"' for v in VERSIONS)
    with open("all_repos_all_versions.toml", "w") as f:
        f.write(f"versions = [{versions_str}]\n")
        f.write("\n")
        f.write("[repos]\n")
        f.write('odoo = ["odoo"]\n')
        for org, repo_versions in org_repo_versions.items():
            write_toml_org_section(f, org, repo_versions, all_versions=True)
    print("Wrote all_repos_all_versions.toml")


if __name__ == "__main__":
    main()
