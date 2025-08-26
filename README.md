# mel — friendly git abstraction for non‑engineers

Many non-engineers have contributions for codebases (static sites, docs, design tweaks, image swaps, etc.) and the learning curve on git is steep.

`mel` is a simplification of a common git flow that makes versioned collaboration more approachable for those non-engineer contributors.

**Mission: enable non-engineers to contribute!**

## Install

**macOS/Linux (no sudo).** On macOS installs to `/opt/homebrew/bin` or `/usr/local/bin` when writable; otherwise to `~/.local/bin`.

```bash
curl -fsSL https://raw.githubusercontent.com/davefowler/melcurial/main/install.sh | bash
```

## Usage

### For non-engineers

Use these commands in your project folder. Plain language, safe defaults, and helpful prompts.

```bash
mel save "message"  # saves (optionally using your message), updates with main, and pushes
mel status          # shows what's going on
mel reset           # reset your workspace to the latest main (clean slate)
mel publish         # runs checks and ships your changes to main
```

**Tips:**
- If mel asks what to do with local changes, choose Save or Stash.
- If mel asks to confirm adding files, review the list and type `y` to continue.
- If mel offers to open a pull request, say yes and follow the link.

### For engineers

`mel` is also a great tool for engineers who want a smooth, quick workflow. Toggle to advanced mode with `mel mode advanced`.

```bash
mel save "message"  # commit-all (use message if provided) → rebase onto main → push
mel update          # get latest changes from main
mel status          # show ahead/behind, dirty files, last commit + git status
mel publish         # FF merge to main → push → rebase branch
mel diff            # show staged/unstaged diff stats
mel open repo       # open remote repo page in your browser
mel open branch     # open current branch page in your browser
mel open pr         # open compare PR URL (GitHub) in your browser
mel reset           # hard reset workspace branch to latest main and force‑push
mel <name>          # run configured or package script; supports `--` for extra args
```

## How it works

`mel` is just a wrapper around git. It keeps each person working in their own branch, and automatically pulling in changes from the main branch. If at any point someone gets stuck you can revert to directly using git.

## Team setup

`mel` can be tailored to your team's specifics through a `.mel/config_template.json` file. You can add custom scripts, change merge behavior, auto import scripts from packages and more.

For a full description checkout the [configuration documentation](docs/config.html).

## Configuration

mel reads `.mel/config.json` at the repository root. If it's missing, mel will create the `.mel` folder as needed.

### Key settings

- **`main`**: Name of your default branch (auto-detected as `main` or `master`)
- **`update_strategy`**: `rebase` (default) or `merge` for updates
- **`scripts`**: Custom commands callable via `mel <name>`
- **`allow_package_scripts`**: If true, fall back to package manager scripts
- **`open_pr_on_sync`**: Open PR URL after `mel sync` (GitHub)
- **`contributor_mode`**: `basic` (default) or `advanced` help text
- **`require_add_confirmation`**: Show file list before adding (default: true)
- **`require_publish_confirmation`**: Confirm before publishing (default: true)

### Quick mode switching

Use `mel mode basic` or `mel mode advanced` to change help text without editing config.

### Example config

```json
{
  "main": "main",
  "update_strategy": "rebase",
  "open_pr_on_sync": true,
  "scripts": {
    "test": "pytest -q --disable-warnings",
    "build": "npm run build -s"
  },
  "allow_package_scripts": true,
  "contributor_mode": "advanced"
}
```

## Development

This project uses mel for version control. Use `mel save`, `mel sync`, `mel publish` etc. instead of raw git commands.

## Installation options

### Quick install (recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/davefowler/melcurial/main/install.sh | bash
```

### With pipx (for Python users)
```bash
pipx install git+https://github.com/davefowler/melcurial.git
```

### With pip (user site)
```bash
python3 -m pip install --user git+https://github.com/davefowler/melcurial.git
```

### Manual install
```bash
curl -fsSL https://raw.githubusercontent.com/davefowler/melcurial/main/mel -o /usr/local/bin/mel
chmod +x /usr/local/bin/mel
```

## Quick start

```bash
# From an existing Git repo
mel save "my first change"     # creates workspace branch if needed
# edit files...
mel status                      # view state at a glance
mel publish                     # ship your changes to main
```

## Non-interactive mode

For automation, set `MEL_YES=1` (or pass `--yes`) to answer "yes" to confirmations and choose safe defaults.

## Safety features

- `save` is disabled on main to prevent accidental commits
- `publish` uses fast-forward merges only
- `reset` refuses to run on main
- File confirmation before adding (configurable)
- Publish confirmation (configurable)

## Documentation

- **[Home](docs/index.html)** - Overview and quick start
- **[Configuration](docs/config.html)** - Full config options and examples
- **[Explained](docs/explained.html)** - Detailed command explanations
- **[About](docs/about.html)** - The story behind mel

## Contribute

Right now we need users and feedback! If you have requests, ideas, or contributions, please file an [issue](https://github.com/davefowler/melcurial/issues) or [PR](https://github.com/davefowler/melcurial/pulls) on [GitHub](https://github.com/davefowler/melcurial).

## License

Use at your own risk. Adapt freely.


