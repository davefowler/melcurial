## mel – configuration and advanced options (for engineers)

### Config file
mel reads `.mel/config.json` at the repo root. If missing, mel will create the `.mel` folder as needed.

Supported fields:
- `main`: string – default branch name. Auto‑detected as `main` or `master` if absent.
- `user_branch`: string – last branch created via `mel start` (managed by mel).
- `test_commands`: string[] – shell commands to run for `mel test` and pre‑publish checks.
- `example_test_commands`: string[] – example commands shown by mel; ignored if `test_commands` is set.
- `update_strategy`: `"rebase" | "merge"` – strategy for `pull`, `update`, and `sync` (default: `rebase`).
- `open_pr_on_sync`: boolean – if true, open an auto‑generated PR URL after `mel sync` (GitHub supported).
- `merge_message`: string – merge commit message template. Supports `{branch}`, `{main}`, `{author}`, `{datetime}`.
- `merge_message_after_sync`: string – optional template used for merges triggered by `sync`.

Example:
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
  "merge_message_after_sync": "Merge {branch} into {main}",
  "example_test_commands": ["npm ci && npm test -s", "pytest -q --disable-warnings"]
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


