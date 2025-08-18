## mel — a tiny helper for non‑engineers

mel is a single‑file CLI that wraps a few safe Git workflows in friendly commands. It was originally built to help a marketing teammate (Mel!) manage a static site without learning Git internals.

### Highlights
- **start**: create or reset a feature branch based on your main branch. If you don't pass a name, mel will prompt you and sanitize it into a safe branch name.
- **save**: stage, commit, rebase on latest main, and push your branch.
- **publish**: run tests, fast‑forward merge your branch into main, push, and rebase your branch back onto main.
- **reset**: hard‑reset your current feature branch back to main's tip and force‑push.
- **sync**: one‑shot “save/stash, update with main via rebase or merge, push”.
- **update**: alias of `pull`; in docs for non‑engineers we recommend `update` over `pull`.
- **open**: open the repo, current branch or PR in your remote.
- **diff**: quick diff stats of staged/unstaged changes.
- **status**: show mel config, current branch info, ahead/behind counts, dirty files, and last commit, plus `git status -sb`.
- **pull**: update main or fast‑forward merge latest main into your current branch, with an interactive prompt to handle uncommitted changes.
- **test hooks**: configure project‑specific test commands in `.mel/config.json`.

### Installation

Quick install (macOS/Linux):
```bash
curl -fsSL https://raw.githubusercontent.com/davefowler/melcurial/main/install.sh | bash
```

Notes:
- Installs `mel` to `/usr/local/bin` if writable; otherwise to `~/.local/bin`.
- If the chosen directory is not on your PATH, the script prints a snippet to add.
- Requires `curl` and `python3`.

Install with pipx (recommended for Python users):
```bash
pipx install git+https://github.com/davefowler/melcurial.git
```

Install with pip (user site):
```bash
python3 -m pip install --user git+https://github.com/davefowler/melcurial.git
```

Manual install:
```bash
curl -fsSL https://raw.githubusercontent.com/davefowler/melcurial/main/mel -o /usr/local/bin/mel
chmod +x /usr/local/bin/mel
```

### Quick start
```bash
# From an existing Git repo
mel start my-landing-update     # or just: mel start (will prompt for your name)
# edit files...
mel sync                        # save/stash, update with main, push
mel status                      # view state at a glance
mel publish                     # run tests, fast‑forward merge into main, push
```

### Commands
- **start [name]**: Create or reset `branch` (sanitized from `name`) from the latest main and push with upstream. If omitted, mel prompts for your name.
- **save**: Commit all changes with a timestamped message, fetch, rebase on main, and push.
- **sync**: Save or stash as needed, update with latest main using the configured strategy (defaults to rebase), and push. Optionally opens a PR.
- **publish**: Confirm, re‑run tests, update local main, fast‑forward merge your branch into main, push main, then rebase your branch on main and push again.
- **reset**: For feature branches only. Hard‑reset to latest main and force‑push.
- **update | pull**: Update main or update your feature branch with latest main using the configured strategy.
- **diff**: Show staged/unstaged diff stats.
- **open [repo|branch|pr]**: Open your remote in the browser.
- **status**: Prints summary JSON including `main`, `user_branch`, `current_branch`, ahead/behind counts, dirty file count, last commit, then shows `git status -sb`.
- **pull**: If on `main`, `git pull --ff-only`. If on a feature branch, fast‑forward merge latest main into the branch. If you have local changes, mel offers: save first, stash+drop, or cancel.
- **test**: Runs the configured test commands. If none are configured, falls back to a legacy backend/frontend routine (if those paths exist). Otherwise skips tests.

### Configuration (for engineers)
mel stores configuration in `.mel/config.json` at your repo root. If it doesn’t exist, it’s created when you run mel.

Fields:
- `main` (string): Your default branch name. Auto‑detected between `main` or `master` if not set.
- `user_branch` (string): The last branch created via `mel start`.
- `test_commands` (array of strings): Shell commands to run for `mel test` and the pre‑publish step.
- `example_test_commands` (array of strings): Shipped examples; ignored if `test_commands` is set.
- `update_strategy` (string): `rebase` (default) or `merge` for `pull/update/sync`.
- `open_pr_on_sync` (boolean): If true, open a PR URL after `mel sync` (GitHub remotes supported).
- `merge_message` (string): Template for merge commits. Supports `{branch}`, `{main}`, `{author}`, `{datetime}`.
- `merge_message_after_sync` (string): Optional override template used for merges run by `sync`.

Example `.mel/config.json`:
```json
{
  "main": "main",
  "update_strategy": "rebase",
  "test_commands": [
    "npm ci && npm test -s",
    "pytest -q --disable-warnings"
  ],
  "open_pr_on_sync": true,
  "merge_message": "Merge {branch} into {main} by {author} @ {datetime}",
  "merge_message_after_sync": "Merge {branch} into {main}"
}
```

Notes:
- Each entry in `test_commands` is executed as‑is. If any returns non‑zero, tests are considered failed.
- If `test_commands` is missing and no legacy layout is found, tests are skipped.

### Safety and behavior
- `start` creates or resets the target branch based on the latest `main` (local or `origin/main` if available) and sets upstream.
- `save` is disabled on `main` to prevent accidental commits there.
- `publish` uses fast‑forward merges only; if that’s not possible, it aborts with guidance.
- `reset` refuses to run on `main`.

### Troubleshooting
- “No 'origin' remote found. Skipping fetch.” → mel works without a remote, but some features (push, pull) require `origin`.
- Ahead/behind shows “?” → likely no upstream is set. `mel start` sets it automatically; otherwise run `git push -u origin HEAD`.

### Ideas to extend
- Pre/Post hooks: `pre_save`, `post_save`, `pre_publish`, `post_publish` commands in config.
- PR helper: `mel pr` (covered by `mel open pr`).
- Dry‑run mode: `MEL_DRY_RUN=1` to print commands without executing.
- Auto‑stash/restore option on `pull` instead of drop.
- Protected branches list in config.

### License
Use at your own risk. Adapt freely.


