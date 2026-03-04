#!/usr/bin/env python3
"""Fetch OCA repos and generate TOML/YAML files tracking which versions each repo supports."""

import os
import requests

VERSIONS = ["12.0", "13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"]

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


def get_repo_branches(repo_name):
    branches = set()
    try:
        for branch in paginate(f"https://api.github.com/repos/OCA/{repo_name}/branches"):
            branches.add(branch["name"])
    except requests.HTTPError as e:
        print(f"Warning: could not fetch branches for {repo_name}: {e}")
    return branches


def main():
    print("Fetching OCA repos...")
    repos = get_oca_repos()
    print(f"Found {len(repos)} repos")

    version_repos = {v: [] for v in VERSIONS}
    repo_versions = {}

    for i, repo in enumerate(sorted(repos), 1):
        print(f"[{i}/{len(repos)}] Checking {repo}...")
        branches = get_repo_branches(repo)
        versions_for_repo = [v for v in VERSIONS if v in branches]
        repo_versions[repo] = versions_for_repo
        for v in versions_for_repo:
            version_repos[v].append(repo)

    # Write per-version TOML files
    for version in VERSIONS:
        filename = f"all_repos_{version}.toml"
        oca_repos = sorted(version_repos[version])
        with open(filename, "w") as f:
            f.write(f'versions = ["{version}"]\n')
            f.write("\n")
            f.write("[repos]\n")
            f.write('odoo = ["odoo"]\n')
            f.write("oca = [\n")
            f.write("  # addons repositories\n")
            for repo in oca_repos:
                f.write(f'  "{repo}",\n')
            f.write("]\n")
        print(f"Wrote {filename} ({len(oca_repos)} repos)")

    # Write aggregate YAML file
    with open("all_repos_all_versions.yml", "w") as f:
        for repo in sorted(repo_versions):
            versions = repo_versions[repo]
            if versions:
                versions_str = ", ".join(f'"{v}"' for v in versions)
                f.write(f'- ["{repo}", [{versions_str}]]\n')
    print("Wrote all_repos_all_versions.yml")


if __name__ == "__main__":
    main()
