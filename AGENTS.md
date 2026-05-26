# AGENTS.md

## Project scope

- This repository is for `gacha-release-alert`: collecting Japanese gacha / lottery release data, exporting `public/data/releases.json`, and deploying the static GitHub Pages dashboard.
- Keep discussion and repository work focused on this project when operating from the related Discord channel/thread.
- Do not commit local/private runtime configuration or secrets, especially `config.yaml`, `filters.yaml`, Discord webhook URLs, local SQLite/cache files under `data/`, virtualenvs, or generated tool caches.

## Standard workflow for repository tasks

1. Start by confirming repository state:
   - `git status --short --branch`
   - `git remote -v`
   - `git fetch origin` / `git pull --ff-only origin main` when practical.
2. Make the smallest focused change that satisfies the request.
3. Before staging, inspect the intended changes:
   - `git diff --stat`
   - targeted `git diff -- <path>` for edited files.
4. Run relevant verification before committing:
   - `python -m pytest`
   - `python -m ruff check src tests` when `ruff` is available.
   - There is currently no npm build/test flow in this Python/static repo; if a future `package.json` adds scripts, run the relevant build/test/lint scripts too.
5. Commit finished changes with a concise conventional commit message.
6. Push the commit to the configured remote branch.
7. After pushing, check the GitHub Actions result for the pushed commit. If it fails, analyze the logs, fix the root cause, verify locally again, commit, push, and repeat until Actions passes or a repo/platform permission issue blocks completion.
8. Finish by reporting the commit SHA, Actions status/URL, and final working-tree state.

## GitHub Actions / Pages notes

- `.github/workflows/pages.yml` runs on `workflow_dispatch`, a 6-hour schedule, and pushes to `main`.
- Scheduled/manual runs fetch data with `config.pages.yaml`, export `public/data/releases.json`, commit the data when changed, and deploy `public/` to GitHub Pages.
- `public/data/releases.json` is intentionally tracked even though the local cache directory `data/` is ignored. If the workflow stages release data, use `git add -f public/data/releases.json` so broad ignore rules do not break the scheduled job.
- For Pages deployment failures, verify the repository Settings → Pages source is set to **GitHub Actions** and inspect failed workflow logs before changing code.

## Source/data expansion guidelines

- For new brands or sources such as Takara Tomy Arts, Qualia, or Ken Elephant, first document the public data surface and confirm it can be fetched periodically without login, CAPTCHA, or terms-of-service issues.
- Add fixture-backed parser tests for every new HTML/API source before relying on it in scheduled collection.
- Preserve source attribution and stable dedupe keys. If vendor item IDs are absent or unstable, dedupe semantically by source + normalized title/character while keeping original URLs.
- Avoid making the scheduled workflow depend on brittle browser automation unless no lightweight HTTP/RSS/API surface exists.
