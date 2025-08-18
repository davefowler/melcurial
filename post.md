### Meet mel: a tiny CLI that makes Git feel like a CMS

Years ago, I built a small script for our head of marketing, Mel. She needed to publish changes to our static site without learning Git’s foot‑guns. Out of that came “melcurial” — a single‑file CLI that wraps a few safe workflows behind friendly commands.

This post is a refreshed take on that idea. Same spirit, a bit more polish.

### Why bother?

If you ship a static site or docs from Git, you probably want teammates outside of engineering to:
- create a branch
- make edits
- save work to the cloud
- run checks
- merge safely

Git can do all of this, but the UX is not exactly ergonomic. mel narrows the path and makes the happy path obvious.

### What mel does

- start: creates or resets a feature branch based on your main branch. If you don’t pass a name, mel prompts for it and turns it into a safe branch (no weird characters).
- save: stages, commits with a timestamped message, rebases on the latest main, and pushes.
- deploy: re‑runs tests, fast‑forward merges your branch into main, pushes, and rebases your branch back on main.
- freshstart: hard‑resets your feature branch to main’s tip and force‑pushes (a clean slate when you’ve diverged too far).
- status: shows a compact, high‑signal summary (ahead/behind, dirty files, last commit) plus `git status -sb`.
- pull: updates main or fast‑forward merges main into your feature branch, with an interactive prompt to handle local changes.

### Configurable tests

One pain in the first version: test steps were hardcoded for a specific repo. Now mel reads `.mel/config.json` and runs whatever you put in `test_commands`.

Example:
```json
{
  "test_commands": [
    "npm ci && npm test -s",
    "pytest -q --disable-warnings"
  ]
}
```

Each command is executed as‑is. If any fails, deploy is halted with a clear message.

If you don’t configure tests and mel doesn’t detect a legacy layout, it simply skips tests — better than failing obscurely.

### Tiny workflow, big win

The litmus test for mel was: could someone who doesn’t live in Git land make and publish a change without asking for help? With mel, the flow looks like this:

```bash
mel start           # or: mel start my-branch
# edit content
mel save
mel status
mel deploy
```

That’s it. A few commands, safe defaults, and clear output.

### Future ideas

- Pre/Post hooks: `pre_save`, `post_save`, `pre_deploy`, `post_deploy`.
- `mel pr` to open a pull request for the current branch.
- Dry‑run mode to print commands without executing.
- Protected branches in config to prevent foot‑guns.

### Grab it

It’s a single script. Drop it on your PATH, make it executable, and go. The goal isn’t to replace Git — it’s to make the happy path feel obvious and friendly.


