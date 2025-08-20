## mel – configuration and advanced options (for engineers)

### Config file
mel reads `.mel/config.json` at the repo root. If missing, mel will create the `.mel` folder as needed.

Notes:
- When mel writes the config (e.g., via `mel start`), it will ensure `.mel/` is listed in your repository `.gitignore` if that file exists. This keeps user‑specific state like `user_branch` local and avoids conflicts between collaborators.
- You can still check in a template config if desired (e.g., in docs), but the per‑user `.mel/config.json` is generally meant to remain untracked.

Supported fields:
- `main`: string – default branch name. Auto‑detected as `main` or `master` if absent.
- `user_branch`: string – last branch created via `mel start` (managed by mel).
- `update_strategy`: `"rebase" | "merge"` – strategy for `pull`, `update`, and `sync` (default: `rebase`).
- `open_pr_on_sync`: boolean – if true, open an auto‑generated PR URL after `mel sync` (GitHub supported).
- `merge_message`: string – merge commit message template. Supports `{branch}`, `{main}`, `{author}`, `{datetime}`.
- `merge_message_after_sync`: string – optional template used for merges triggered by `sync`.
- `scripts`: object – custom commands callable via `mel run <name>` and used by `mel test` when you define `scripts.test`.
- `allow_package_scripts`: boolean – if true, `mel run <name>` falls back to `<pm> run <name>` when not found in config (pm = npm/yarn/pnpm). Also enables `mel test` to fall back to `<pm> run test`. Default: `true`.

Example:
```json
{
  "main": "main",
  "update_strategy": "rebase",
  "scripts": {
    "test": "pytest -q --disable-warnings"
  },
  "open_pr_on_sync": true,
  "merge_message": "Merge {branch} into {main} by {author} @ {datetime}",
  "merge_message_after_sync": "Merge {branch} into {main}",
  "scripts": {
    "build": "npm run build -s",
    "publish-site": { "cmd": "npm run deploy", "cwd": "site", "env": { "NODE_ENV": "production" } },
    "reindex": { "cmd": "python tools/reindex.py --all" }
  },
  "allow_package_scripts": false
}
```

### Update behavior
By default, mel rebases feature branches on top of the latest `main`. To switch to a merge workflow, set `update_strategy` to `"merge"`. When using merge, you can provide `merge_message` templates.

### Uncommitted changes handling
When updating, mel prompts to:
- Save: commit current changes
- Stash: stash before update and re‑apply afterwards
- Cancel

### Non‑interactive mode
For automation/CI or scripts, mel supports a non‑interactive mode that answers yes to confirmations and chooses safe defaults for prompts:
- Env var: `MEL_YES=1`
- Flag: `--yes`

This affects commands like `publish`, `reset`, and `sync` (chooses Save when prompted about uncommitted changes).

### Extra commands for engineers
- `mel diff` – Show staged/unstaged diff stats quickly.
- `mel open [repo|branch|pr]` – Open remote repository pages in a browser.
- `mel scripts` – List script names from `.mel/config.json`.
- `mel run <name> [-- args...]` – Run a configured script. If `allow_package_scripts` is true and the script is not in config, mel will run `<pm> run <name>` (pm auto‑detects pnpm/yarn/npm).

### Hooks (optional)
You can run commands before/after core operations by adding hook arrays to config. Each entry can be a string (script name or raw shell) or an object `{ cmd, cwd?, env? }`.
- `pre_save`, `post_save`
- `pre_sync`, `post_sync`
- `pre_publish`, `post_publish`

If a hook command returns a non‑zero exit code, the main operation aborts.


