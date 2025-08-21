## Mercurial (Hg) Support Plan

### Goals
- **Abstract VCS operations** behind a common interface.
- **Auto-detect** Git vs Mercurial with config/env overrides.
- **Preserve UX** and semantics where possible; **degrade gracefully** when exact parity doesn’t exist.
- **No behavior change for Git** users during the refactor.

### Detection Strategy
- Order of precedence:
  - **Env override**: `MEL_VCS=git|hg`.
  - **Config override**: `.mel/config.json` key `"vcs"` = `"git" | "hg"`.
  - **Repository markers**: nearest ancestor of CWD containing `.git/` → Git, `.hg/` → Hg.
  - **Command probes**: `git rev-parse --show-toplevel` or `hg root` (non-interactive) if markers absent.
  - If both `.git` and `.hg` found (rare), prefer env/config or the closest ancestor marker.

### VCS Abstraction (shape)
A minimal, capability-driven surface that all commands use. Git maps 1:1; Hg implements best-fit.

```python
class VCSBackend(Protocol):
    def repo_root(self) -> str: ...
    def current_workspace(self) -> str: ...
    def base_branch_name(self) -> str: ...  # e.g. "main" (Git), "default" (Hg)

    def primary_remote_name(self) -> str: ...
    def has_remote(self, remote: str | None = None) -> bool: ...
    def remote_web_url(self) -> str | None: ...

    def fetch(self) -> None: ...
    def checkout_workspace_on_base(self, workspace: str, base: str) -> None: ...
    def ensure_tracked_and_commit_all(self, message: str) -> None: ...
    def push_current(self, set_upstream: bool) -> None: ...

    def rebase_onto(self, base_ref: str) -> None: ...
    def merge_ff_only(self, ref: str) -> None: ...  # emulate in Hg or fall back
    def hard_reset_to(self, base_ref: str) -> None: ...

    def status_porcelain(self) -> str: ...
    def short_status(self) -> None: ...
    def ahead_behind(self) -> tuple[int | str, int | str]: ...  # '?' when unknown
    def upstream_ref(self) -> str | None: ...

    # Optional (if available):
    def stash_push(self, name: str) -> bool: ...
    def stash_pop(self) -> int: ...
```

### Git Backend Mapping (baseline)
- Implement `GitVCS` using existing functions (no behavior change):
  - `repo_root`, `current_branch`→`current_workspace`, `guess_main_name`→`base_branch_name`.
  - `fetch_origin`→`fetch`, `push_current`, `rebase_onto`, `merge_ff_only`, `get_origin_web_url`→`remote_web_url`, etc.
- All current commands call the backend instead of raw `git` commands.

### Mercurial Backend Design
- **Workspace representation**: use **bookmarks** by default (fallback to named branches when no bookmark is active).
- **Main branch**: default to `default` when `main` not specified in `.mel/config.json`.
- **Remote name**: `default` from `hg paths` (no upstream tracking like Git).
- **Rebase/shelve**: use when available; otherwise provide merge/safe fallbacks with clear messages.

Command mappings (Hg):
- repo root: `hg root`
- current workspace: active bookmark via `hg log -r . --template "{bookmarks}"` or `hg summary`; else `hg branch`.
- has remote: `hg paths` contains `default` (or configured path name).
- fetch: `hg pull`.
- checkout workspace on base:
  - `hg pull` → `hg update <base>` → `hg bookmark -f <workspace>` → `hg update <workspace>`.
- commit all: `hg addremove` → `hg commit -m <msg>` (handle no-change exit code).
- push current: `hg push` (no upstream flags).
- rebase onto: `hg rebase -d <base>` if extension present; else fallback to merge path.
- fast-forward merge only: emulate via rebase if possible; else prompt/merge.
- hard reset to base: move bookmark to base tip (`hg update <base>`; `hg bookmark -f <workspace>`; `hg update -C <workspace>`). For divergent histories, prefer `hg rebase` with warnings.
- porcelain/short status: `hg status`, `hg summary`.
- ahead/behind: count `hg outgoing -q` and `hg incoming -q` (return `?` when remote missing).
- stash: `hg shelve -n <name>` / `hg unshelve` if `shelve` extension available; otherwise hide stash option.

Open operations:
- remote URL: `hg paths default` → normalize SSH/HTTPS to web URL (Bitbucket/GitHub Enterprise/GitLab mirrors if applicable).
- open repo/branch: derive host-specific branch URL when recognized; otherwise open repo root.
- opening PRs: initially Git-only; print helpful note under Hg.

### Command Behaviors (Git preserved; Hg specifics)
- **start**
  - Hg: pull, `update <default>`, create/force bookmark `<workspace>`, switch to it, push on first save.
- **save**
  - Hg: `addremove`; commit; update via strategy:
    - `rebase` (default): `hg rebase -d <default>` if available, else message+merge fallback.
    - `merge`: `hg pull && hg update <workspace> && hg merge <default> && hg commit -m ...`.
  - Push current.
- **publish**
  - Hg: run tests; `hg pull && hg update <default>`; merge workspace into default; commit; push; switch back to workspace; rebase onto default if available.
  - Note: no strict FF-only; document behavior.
- **reset**
  - Hg: destructive move of bookmark to default tip and clean working copy; prefer rebase to linearize when needed; print safety warnings.
- **status**
  - Hg: `hg summary` plus `hg status`; show incoming/outgoing counts as ahead/behind.
- **pull/update/sync**
  - Hg: offer save/shelve/cancel (hide shelve if unavailable); apply strategy like `save`.
- **diff**
  - Hg: `hg diff --stat` (no staged vs unstaged separation).

### Config Surface
- `.mel/config.json` additions:
  - `"vcs"`: `"git" | "hg"` (optional override).
  - `"hg_mode"`: `"bookmarks" | "branches"` (default `"bookmarks"`).
  - `"main"`: respected for both; default `"main"` for Git, treated as `"default"` for Hg when absent.
  - Existing flags (e.g., `"update_strategy"`, `"require_add_confirmation"`, hooks) apply to both backends.
- Env: `MEL_VCS` temporary override.

### Implementation Steps (Milestones)
1. **Introduce backend layer**
   - New `vcs.py` with `VCSBackend`, `GitVCS`, `HgVCS`, and `detect_vcs(root)`.
   - Wire detection into `mel`; pass a backend instance to all command handlers.
2. **Refactor to Git backend**
   - Replace direct Git calls with backend methods; parity with current behavior.
3. **Add Hg backend (core flows)**
   - Implement `start`, `save`, `status`, `diff`, `pull/update/sync` using bookmarks.
4. **Hg publish/reset nuances**
   - Implement merge-to-default + push; rebase/merge fallback logic; destructive reset safeguards.
5. **Finish UX polish**
   - Clear messaging when extensions (`rebase`, `shelve`) are missing.
   - URL opening support for common hosts.
6. **Docs & tests**
   - Update help/docs to describe Hg behavior and differences.
   - Parametrize tests by backend; run Hg tests conditionally when `hg` is available.

### Risks and Edge Cases
- Hg without `rebase`/`shelve`: reduce functionality gracefully; include guidance to enable extensions.
- Mixed repos containing both `.git` and `.hg`: require explicit override or nearest marker heuristic.
- Ahead/behind in Hg is approximate via incoming/outgoing counts.
- No staging area in Hg: adapt `diff` and add/commit flows accordingly.

### Minimal Detection Snippet (conceptual)
```python
def detect_vcs(start: str) -> VCSBackend:
    forced = os.getenv("MEL_VCS") or (get_cfg(start).get("vcs") if os.path.exists(os.path.join(start, ".mel", "config.json")) else None)
    if forced == "git":
        return GitVCS()
    if forced == "hg":
        return HgVCS()

    root = ascend_until_marker(start, [".git", ".hg"])  # nearest ancestor with marker
    if root and os.path.exists(os.path.join(root, ".git")):
        return GitVCS()
    if root and os.path.exists(os.path.join(root, ".hg")):
        return HgVCS()

    if run(["git", "rev-parse", "--show-toplevel"], check=False)[0] == 0:
        return GitVCS()
    if run(["hg", "root"], check=False)[0] == 0:
        return HgVCS()
    raise SystemExit("Not a Git or Mercurial repository")
```

### Notes
- Keep Git UX identical; Hg commands should feel equivalent but may print notes where behavior differs (e.g., no FF-only).
- Start with a small PR refactor (backend layer + Git); follow with Hg in incremental PRs.
