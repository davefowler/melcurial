# Plugin System – Design Answers

This document captures design decisions and recommendations for Mel’s plugin system.

## 1) How do plugins update themselves?

- **Distribution**
  - Core/basics bundled in this repo under `plugin_defaults/<name>` for zero-setup.
  - Optional/advanced plugins live in separate repos (recommended) for independent releases.
  - User/org overrides live in `~/.mel/plugins/<name>`.
- **Installation sources (runtime precedence)**
  1. `plugin_defaults/<name>` (bundled)
  2. `~/.mel/plugins/<name>` (user/org override)
  3. `.mel/plugins/<name>` (repo-local)
  4. Template `.mel/config_template.json` (scripts/hooks/config only)
  5. User `.mel/config.json` (highest precedence for scripts/hooks/config)
- **Updating**
  - Runtime merging means updates propagate on next run without copying.
  - CLI updates refresh `plugin_defaults/` → users get new defaults automatically.
  - Admins can deploy org-wide plugins or overrides in `~/.mel/plugins`.
  - Remote install (future): `mel plugin install <git-url>` clones to `~/.mel/plugins/<name>`.
- **Versioning**
  - Each plugin should include a `version` field in `config.json`.
  - Optional `VERSION` file or git tag for external repos.
  - `mel plugin update [name]` can pull latest from the plugin’s origin (once remote support exists).

## 2) Auto-detecting VCS plugins

- On first run, detect `.git` or `.hg` and auto-install the matching plugin (from defaults or user path).
- Add the plugin name to the runtime plugin list (no hard copy), then load/merge configs each run.
- If the plugin isn’t available, print instructions to install (`mel plugin install git|hg`).

## 3) Docs as a plugin

- Yes: `mel-docs` is a plugin. It contains:
  - `config.json` with a `docs` command (advanced mode).
  - `bin/docs.sh` to serve content.
  - Optionally its own templates/assets; serve from within the plugin directory or the repo’s `docs/`.
- Project-level docs builder (`scripts/build_docs.py`) remains for building static site pages. The plugin offers a simple local server.

## 4) Executables in plugins

- Each plugin may have `bin/` for executables referenced by `config.json` commands.
- Commands should be short shell lines; complex logic should live in `bin/` scripts.
- Executables are made `+x` during plugin install.

## 5) Archiving old artifacts

- Move legacy Python CLI, old tests, and old templates/docs to `archive/` to avoid confusion while the new system lands.
- Keep new plugin-based docs/assets within each plugin or within top-level `docs/` for project docs.

## 6) Docs templates location

- If docs are a plugin feature, their templates/assets belong inside the plugin folder.
- If they’re project docs (marketing/overview/specs), they belong in top-level `templates/` and `docs/`.
- The `mel-docs` plugin should be self-contained enough to function in any repo.

## 7) Dependencies and runtime environment

- Prefer zero external deps for plugins; shell-first. When needed:
  - Declare requirements in a `requires` section inside `config.json` (e.g., `{ "requires": { "python": ">=3.10", "pip": ["jinja2>=3.1"] } }`).
  - On first command run, the plugin can bootstrap a venv in `.mel/plugins/<name>/.venv` and `pip install` its deps.
  - Allow override of interpreter via `MEL_PYTHON` env; default to `/usr/bin/env python3`.
  - Optionally share a cache in `~/.mel/plugins/<name>/.venv`.
- Failure modes should be helpful (missing python/jinja2 → actionable error).

## Remote plugin registry (future)

- Support `mel plugin install <git-url>` and a simple registry JSON mapping slugs → git URLs.
- Validate `config.json` schema on install to avoid broken plugins.

## Security considerations

- Plugins are executable code. Recommend pinning versions and reviewing external sources.
- Consider a `--yes` flag or `MEL_YES=1` to bypass confirmations.

## Summary

- Plugins are file-based, versionable, and loaded at runtime from defaults, user-home, and repo-local paths.
- No hard copies; admins can update centrally and users pick up changes automatically.
- Clear separation: project docs vs plugin docs; plugin `bin/` for logic; simple remote install in future.

