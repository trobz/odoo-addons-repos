# odoo-addons-repos

A registry of [OCA](https://github.com/OCA) (and select non-OCA) Odoo addon repositories, auto-updated daily and published as TOML files for use with [local.py (tlc)](https://github.com/trobz/local.py).

## Purpose

This repository tracks which OCA addon repos exist and which Odoo versions each one supports (12.0 → 19.0). It generates ready-to-use TOML files that can be included in a `tlc` config to clone or update a full set of addon repositories for a given Odoo version.

## Files

| File | Description |
|---|---|
| `all_repos_<version>.toml` | All repos supporting a specific Odoo version (e.g. `all_repos_17.0.toml`) |
| `all_repos_all_versions.toml` | All repos across all versions, with per-repo version lists |
| `update.py` | Script that queries the GitHub API and regenerates the TOML files |

## How it works

1. `update.py` queries the GitHub API for all repositories in the `OCA` organization (plus a small set of extra repos from other orgs).
2. For each repo, it checks which version branches exist (e.g. `17.0`, `18.0`).
3. It writes one `all_repos_<version>.toml` per supported version, listing every repo that has a branch for that version.
4. A GitHub Actions workflow runs this script every day at midnight UTC and opens a PR if any changes are detected. PRs are auto-merged.

## Tracked organizations

| Org | Scope |
|---|---|
| `OCA` | All repos (excluding OCB, OpenUpgrade, localizations except `l10n-france`, and a few utility repos) |
| `camptocamp` | `odoo-cloud-platform` |
| `forgeflow` | `stock-rma` |

## Stay notified of new OCA repos

**Watch this repository** to be notified whenever new OCA repositories are added or removed. Each time OCA publishes a new addon repository, the daily workflow will pick it up and merge an update PR here.
