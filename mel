#!/usr/bin/env python3

import json, os, subprocess, sys, datetime, shlex, re, platform, urllib.request, urllib.error

# -----------------------------
# Shared help text (single source of truth for CLI and docs)
# -----------------------------


HELP_BASIC = """Basic commands:
  mel save "message"  # saves your changes and gets the latest from others
  mel status          # shows what changes you've made since saving
  mel publish         # save and publish your work to main
  mel reset           # ditch your changes and start over from main

Troubleshooting:
  If you get "uncommitted changes" errors, run 'mel clear' to stash them first.
"""

HELP_ADVANCED = """Advanced commands:
  mel b <branch name> # create or switch to branch if existing
  mel save "message"  # save your changes and get the latest from others
  mel update          # rebase on the latest from main
  mel status          # shows what changes you've made since saving
  mel diff            # show staged/unstaged diff stats
  mel open            # open remote repo page in your browser
  mel help            # show this help
  mel pr              # go to the page to make a new PR
  mel clear           # stash your uncommitted changes (worktree + untracked)
  mel reset           # restart your branch from the latest main (force-push)
  mel upgrade         # update mel to the latest version
  mel mode <mode>     # switch between "basic" and "advanced" help text
  mel --version|-v    # show CLI version and executable path
  mel <name>          # run configured or package script; supports `--` for extra args

Troubleshooting:
  If you get "uncommitted changes" errors, run 'mel clear' to stash them first."""

# Header and section blocks intentionally include their own leading newlines
# so they can be concatenated directly.
HELP_HEADER = """
mel — a simpler git abstraction so non-engineers can contribute

""".strip()

HELP_FOOTER = """
  
Docs: https://davefowler.github.io/melcurial/
GitHub: https://github.com/davefowler/melcurial

Tip: hide underlying git commands (default). To show them, set
  - .mel/config.json → { "print_commands": true }
  - or environment   → MEL_VERBOSE=1
"""



CONFIG_DIRNAME = ".mel"
CONFIG_FILENAME = "config.json"

# CLI version. When packaged, keep in sync with pyproject.toml.
VERSION = "0.1.0"

# Controls whether shell commands are echoed ("→ ...").
# Default: disabled; can be enabled via MEL_VERBOSE=1 or config print_commands=true
PRINT_CMDS = (os.environ.get("MEL_VERBOSE") == "1")

def run(cmd, check=True, cwd=None, env=None):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    if PRINT_CMDS:
        print(f"→ {' '.join(cmd) if isinstance(cmd,list) else cmd}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update({str(k): str(v) for k, v in env.items()})
    proc = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, env=merged_env)
    out_lines = []
    for line in proc.stdout:
        print(line, end="")
        out_lines.append(line)
    rc = proc.wait()
    if check and rc != 0:
        # Create a more informative error message
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        output = "".join(out_lines)
        error_msg = f"Command failed: {cmd_str}\nOutput: {output}"
        raise subprocess.CalledProcessError(rc, cmd, error_msg)
    return rc, "".join(out_lines)

def repo_root():
    rc, out = run(["git", "rev-parse", "--show-toplevel"])
    return out.strip()

def current_branch():
    rc, out = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip()

def has_remote(remote="origin"):
    rc, out = run(["git", "remote"], check=False)
    return remote in out.split()

def guess_main_name():
    for candidate in ["main", "master"]:
        rc, out = run(["git", "ls-remote", "--heads", "origin", candidate], check=False)
        if out.strip():
            return candidate
    for candidate in ["main", "master"]:
        rc, out = run(["git", "branch", "--list", candidate], check=False)
        if out.strip():
            return candidate
    return "main"

def load_config(root):
    path = os.path.join(root, CONFIG_DIRNAME, CONFIG_FILENAME)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_config(root, cfg):
    d = os.path.join(root, CONFIG_DIRNAME)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, CONFIG_FILENAME)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"✓ Saved mel config at {os.path.relpath(path, root)}")
    ensure_mel_gitignored(root)

def fetch_origin():
    if has_remote("origin"):
        run(["git", "fetch", "origin"])
    else:
        print("! No 'origin' remote found. Skipping fetch.")

def commit_all(default_msg, root=None):
    # Check if we need to confirm before adding files
    if root:
        cfg = get_cfg(root)
        if cfg.get("require_add_confirmation", True):
            # Show what files will be added
            rc, out = run(["git", "status", "--porcelain"], check=False)
            if rc == 0 and out.strip():
                print("\n📁 Files to be added:")
                for line in out.strip().split('\n'):
                    if line:
                        # Parse git status porcelain format: "XY PATH"
                        # X = status of index, Y = status of work tree
                        if len(line) >= 3:
                            status = line[:2]
                            filename = line[3:].strip()
                            print(f"DEBUG: line='{repr(line)}', status='{repr(status)}', filename='{repr(filename)}'")
                            if status == '??':  # Untracked
                                print(f"  + {filename} (new)")
                            elif status == ' M':  # Modified
                                print(f"  ~ {filename} (modified)")
                            elif status == ' D':  # Deleted
                                print(f"  - {filename} (deleted)")
                            elif status == 'A ':  # Added
                                print(f"  + {filename} (added)")
                            elif status == 'R ':  # Renamed
                                print(f"  ~ {filename} (renamed)")
                            else:
                                print(f"  ? {filename} ({repr(status)})")
                
                yes_mode = (os.environ.get("MEL_YES") == "1" or "--yes" in sys.argv)
                if not yes_mode:
                    print("\n⚠️  Add these files to the commit?")
                    response = input("Type 'y' to continue, anything else to abort: ")
                    if response.lower() != 'y':
                        print("Commit cancelled.")
                        sys.exit(0)
    
    run(["git", "add", "-A"])
    rc, out = run(["git", "commit", "-m", default_msg], check=False)
    if rc != 0:
        print("… Nothing to commit.")

def push_current(set_upstream=True):
    args = ["git", "push"]
    if set_upstream:
        args += ["-u", "origin", "HEAD"]
    run(args, check=True)

def rebase_onto(ref):
    try:
        run(["git", "rebase", ref])
    except subprocess.CalledProcessError:
        print("✖ Rebase hit conflicts. Fix files → git add -A && git rebase --continue, or git rebase --abort.")
        sys.exit(2)

def merge_ff_only(ref):
    try:
        run(["git", "merge", "--ff-only", ref])
    except subprocess.CalledProcessError:
        print("✖ Fast-forward merge not possible. Run 'mel save' then try again.")
        sys.exit(2)

def get_cfg(root):
    cfg_path = os.path.join(root, CONFIG_DIRNAME, CONFIG_FILENAME)
    cfg = load_config(root)
    if not cfg and not os.path.exists(cfg_path):
        # Attempt to import from template if provided
        tpl = load_template_config(root)
        if tpl:
            cfg = tpl
            save_config(root, cfg)
            print("✓ Imported mel config from template")
    if "main" not in cfg:
        cfg["main"] = guess_main_name()
    if "update_strategy" not in cfg:
        cfg["update_strategy"] = "rebase"  # or "merge"
    if "scripts" not in cfg:
        cfg["scripts"] = {}
    if "allow_package_scripts" not in cfg:
        cfg["allow_package_scripts"] = False
    if "require_publish_confirmation" not in cfg:
        cfg["require_publish_confirmation"] = True
    if "require_add_confirmation" not in cfg:
        cfg["require_add_confirmation"] = True
    # contributor_mode controls help visibility; only configurable via .mel/config.json
    if "contributor_mode" not in cfg:
        cfg["contributor_mode"] = "basic"
    # Update command printing preference (env overrides config)
    try:
        global PRINT_CMDS
        cfg_print = bool(cfg.get("print_commands", False))
        PRINT_CMDS = (os.environ.get("MEL_VERBOSE") == "1") or cfg_print
    except Exception:
        pass
    return cfg

def sanitize_branch_name(raw_name):
    # Lowercase and replace spaces/invalid chars with '-'
    name = raw_name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    # Allow only safe chars for branch names
    name = re.sub(r"[^a-z0-9._\-/]", "-", name)
    # Collapse repeats and trim
    name = re.sub(r"-+", "-", name).strip("-")
    if not name or name.upper() == "HEAD":
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"mel-{ts}"
    return name

def open_url(url):
    system = platform.system().lower()
    if system == "darwin":
        run(["open", url], check=False)
    elif system == "windows":
        run(["cmd", "/c", "start", url], check=False)
    else:
        run(["xdg-open", url], check=False)

def get_origin_web_url():
    rc, url = run(["git", "remote", "get-url", "origin"], check=False)
    u = url.strip()
    if not u:
        return None
    m = re.match(r"git@([^:]+):([^/]+)/([^/]+)(\\.git)?$", u)
    if m:
        host, owner, repo = m.group(1), m.group(2), m.group(3)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://{host}/{owner}/{repo}"
    m = re.match(r"https?://([^/]+)/([^/]+)/([^/]+)(\\.git)?/?$", u)
    if m:
        host, owner, repo = m.group(1), m.group(2), m.group(3)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://{host}/{owner}/{repo}"
    return None

def ensure_mel_gitignored(root):
    gi_path = os.path.join(root, ".gitignore")
    if not os.path.exists(gi_path):
        return
    try:
        with open(gi_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return
    normalized = [l.strip() for l in lines]
    if ".mel" in normalized or ".mel/" in normalized:
        return
    # Append an entry to ignore the mel config directory
    needs_newline = (len(lines) > 0 and not lines[-1].endswith("\n"))
    to_append = ("\n" if needs_newline else "") + ".mel/\n"
    with open(gi_path, "a", encoding="utf-8") as f:
        f.write(to_append)
    print("✓ Ensured .mel/ is ignored via .gitignore")

def load_template_config(root):
    # Repo-local templates only
    candidates = [
        os.path.join(root, CONFIG_DIRNAME, "config_template.json"),
        os.path.join(root, CONFIG_DIRNAME, "config.template.json"),
    ]

    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            continue
    return None

def load_package_scripts(root):
    pkg_path = os.path.join(root, "package.json")
    if not os.path.exists(pkg_path):
        return {}
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        scripts = pkg.get("scripts") or {}
        if not isinstance(scripts, dict):
            return {}
        return {k: v for k, v in scripts.items() if isinstance(v, str)}
    except Exception:
        return {}

def get_current_author():
    rc, name = run(["git", "config", "user.name"], check=False)
    return name.strip() or ""

def format_merge_message(cfg, context, branch, main):
    template = None
    if context == "sync":
        template = cfg.get("merge_message_after_sync") or cfg.get("merge_message")
    else:
        template = cfg.get("merge_message")
    if not template:
        return None
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    author = get_current_author()
    return template.format(branch=branch, main=main, author=author, datetime=now)

def run_hooks(cfg, hook_key):
    hooks = cfg.get(hook_key)
    if not hooks:
        return
    if not isinstance(hooks, list):
        print(f"! Ignoring invalid hook list for {hook_key}; expected list.")
        return
    for item in hooks:
        if isinstance(item, str):
            # Treat as a script name first, else raw command
            if item in (cfg.get("scripts") or {}):
                rc = run_script_by_name(cfg, item, extra_args=[])
                if rc != 0:
                    raise subprocess.CalledProcessError(rc, item)
            else:
                rc, _ = run(item, check=False)
                if rc != 0:
                    raise subprocess.CalledProcessError(rc, item)
        elif isinstance(item, dict):
            # Inline command object
            cmd = item.get("cmd")
            if not cmd:
                continue
            cwd = item.get("cwd")
            env = item.get("env")
            rc, _ = run(cmd, check=False, cwd=cwd, env=env)
            if rc != 0:
                raise subprocess.CalledProcessError(rc, cmd)
        else:
            print(f"! Unsupported hook entry type: {type(item)}")

def detect_package_manager(root):
    if os.path.exists(os.path.join(root, 'pnpm-lock.yaml')):
        return 'pnpm'
    if os.path.exists(os.path.join(root, 'yarn.lock')):
        return 'yarn'
    if os.path.exists(os.path.join(root, 'package.json')):
        return 'npm'
    return None  # No package manager detected

def run_script_by_name(cfg, name, extra_args):
    root = repo_root()
    scripts = cfg.get("scripts") or {}
    entry = scripts.get(name)
    if entry is None and cfg.get("allow_package_scripts"):
        pm = detect_package_manager(root)
        if pm is None:
            # No package manager detected, skip package script fallback
            pass
        else:
            args = " ".join(shlex.quote(a) for a in extra_args) if extra_args else ""
            cmd = f"{pm} run {shlex.quote(name)}" + (f" -- {args}" if args else "")
            rc, _ = run(cmd, check=False)
            return rc

    if entry is None:
        print(f"✖ Script '{name}' not found.")
        return 1

    if isinstance(entry, str):
        cmd = entry
        if extra_args:
            cmd = cmd + " " + " ".join(shlex.quote(a) for a in extra_args)
        rc, _ = run(cmd, check=False)
        return rc
    elif isinstance(entry, dict):
        cmd = entry.get("cmd")
        if not cmd:
            print(f"✖ Script '{name}' is missing 'cmd'.")
            return 1
        if extra_args:
            cmd = cmd + " " + " ".join(shlex.quote(a) for a in extra_args)
        cwd = entry.get("cwd")
        env = entry.get("env")
        rc, _ = run(cmd, check=False, cwd=cwd, env=env)
        return rc
    else:
        print(f"✖ Script '{name}' has an unsupported format.")
        return 1

def cmd_start(branch_name):
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]

    # Check for uncommitted changes before switching branches
    rc, out = run(["git", "status", "--porcelain"], check=False)
    if out.strip():
        print("⚠️  You have uncommitted changes:")
        print(out)
        print("\nWhat would you like to do?")
        print("1. Save changes (commit now)")
        print("2. Stash changes and re-apply after branch switch")
        print("3. Cancel branch creation")
        response = input("Enter 1, 2, or 3: ")
        
        if response == "1":
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_all(f"mel save before branch switch @ {ts}", root)
        elif response == "2":
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            print("Stashing changes...")
            run(["git", "stash", "push", "-u", "-m", f"mel branch switch backup @ {ts}"])
            print("✓ Changes stashed. Use 'git stash pop' to restore them after switching branches.")
        elif response == "3":
            print("Branch creation cancelled.")
            sys.exit(0)
        else:
            print("Invalid choice. Branch creation cancelled.")
            sys.exit(1)

    fetch_origin()
    base_ref = f"origin/{main}" if has_remote("origin") else main
    
    try:
        run(["git", "checkout", "-B", branch_name, base_ref])
    except subprocess.CalledProcessError as e:
        print(f"✖ Failed to create/switch to branch '{branch_name}':")
        print(f"  {e}")
        print("\nThis usually happens when:")
        print("  • You have uncommitted changes (try 'mel clear' first)")
        print("  • The branch name conflicts with an existing branch")
        print("  • There are merge conflicts")
        print("\nTry running 'mel clear' to stash your changes, then try again.")
        sys.exit(1)
    
    push_current(set_upstream=True)

    cfg["user_branch"] = branch_name
    save_config(root, cfg)
    print(f"✓ Now on '{branch_name}' (based on {base_ref}).")

def cmd_b(branch_name):
    return cmd_start(sanitize_branch_name(branch_name))

def cmd_branch(branch_name):
    return cmd_b(branch_name)

def cmd_save(message=None):
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    cur = current_branch()

    if cur == main:
        print(f"✖ You’re on '{main}'. Create your workspace branch first (e.g. 'git checkout -b <name>').")
        sys.exit(1)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # pre-save hooks
    try:
        run_hooks(cfg, "pre_save")
    except subprocess.CalledProcessError:
        print("✖ pre_save hook failed. Aborting.")
        sys.exit(1)
    commit_msg = message if (message and isinstance(message, str) and message.strip()) else f"mel save @ {ts}"
    commit_all(commit_msg, root)

    fetch_origin()
    base_ref = f"origin/{main}" if has_remote("origin") else main
    rebase_onto(base_ref)

    push_current(set_upstream=False)
    try:
        run_hooks(cfg, "post_save")
    except subprocess.CalledProcessError:
        print("✖ post_save hook failed.")
    print("✓ Save complete.")

def cmd_deploy():
    # Back-compat alias for publish
    return cmd_publish()

def cmd_publish():
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    user = cfg.get("user_branch")
    cur = current_branch()
    branch = user or cur

    if branch == main:
        print(f"✖ You're on '{main}'. Publish only works from your workspace branch (not main).")
        sys.exit(1)

    # Optional pre-publish hooks (teams can run tests via hooks or scripts)
    try:
        run_hooks(cfg, "pre_publish")
    except subprocess.CalledProcessError:
        print("✖ pre_publish hook failed. Aborting.")
        sys.exit(1)

    yes_mode = (os.environ.get("MEL_YES") == "1" or "--yes" in sys.argv)
    if not yes_mode and cfg.get("require_publish_confirmation", True):
        print("⚠️  Are you sure you want to push everything live?!")
        response = input("Type 'y' to confirm, anything else to abort: ")
        if response.lower() != 'y':
            print("Publish cancelled.")
            sys.exit(0)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_all(f"mel publish pre-commit @ {ts}", root)

    fetch_origin()
    run(["git", "checkout", main])
    if has_remote("origin"):
        run(["git", "pull", "--ff-only", "origin", main])

    merge_ff_only(branch)
    run(["git", "push", "origin", main])

    run(["git", "checkout", branch])
    base_ref = f"origin/{main}" if has_remote("origin") else main
    rebase_onto(base_ref)
    push_current(set_upstream=False)

    try:
        run_hooks(cfg, "post_publish")
    except subprocess.CalledProcessError:
        print("✖ post_publish hook failed.")
    print("✓ Publish complete.")

def cmd_freshstart():
    # Back-compat alias; route to reset
    return cmd_reset()

def cmd_reset():
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    branch = current_branch()
    if branch == main:
        print("✖ Don’t run reset on main.")
        sys.exit(1)

    fetch_origin()
    base_ref = f"origin/{main}" if has_remote("origin") else main

    print(f"!! This will ERASE all commits on {branch} and reset it to {base_ref}")
    yes_mode = (os.environ.get("MEL_YES") == "1" or "--yes" in sys.argv)
    if not yes_mode:
        input("Press Enter to confirm, Ctrl+C to abort…")

    # Stash any local uncommitted changes for safety before resetting
    rc, porcelain = run(["git", "status", "--porcelain"], check=False)
    if porcelain.strip():
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        print("Stashing local changes before reset…")
        run(["git", "stash", "push", "-u", "-m", f"mel reset backup @ {ts}"]) 

    run(["git", "reset", "--hard", base_ref])
    run(["git", "push", "--force", "origin", branch])
    print(f"✓ Branch {branch} reset to {base_ref} and force-pushed.")

def cmd_clear():
    root = repo_root()
    # Stash uncommitted changes (including untracked) without touching branch history
    rc, porcelain = run(["git", "status", "--porcelain"], check=False)
    if not porcelain.strip():
        print("… No local changes to clear.")
        return
    yes_mode = (os.environ.get("MEL_YES") == "1" or "--yes" in sys.argv)
    if not yes_mode:
        resp = input("This will stash your local changes. Type 'y' to continue: ")
        if resp.lower() != 'y':
            print("Clear cancelled.")
            sys.exit(0)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    run(["git", "stash", "push", "-u", "-m", f"mel clear @ {ts}"])
    print("✓ Changes stashed. Use 'git stash list' to view and 'git stash pop' to restore.")

def cmd_status():
    root = repo_root()
    cfg = get_cfg(root)
    cur = current_branch()
    rc, porcelain = run(["git", "status", "--porcelain"], check=False)
    dirty_count = len([l for l in porcelain.splitlines() if l.strip()])
    rc, last_commit = run(["git", "log", "-1", "--pretty=%h %s (%cr)"], check=False)
    # ahead/behind (may fail if no upstream)
    ahead = behind = "?"
    upstream = None
    rc, upstream_out = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], check=False)
    if rc == 0:
        upstream = upstream_out.strip()
    rc, ab = run(["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"], check=False)
    try:
        left, right = ab.strip().split()
        behind, ahead = left, right
    except Exception:
        pass

    print("— mel status —")
    status_obj = {
        "main": cfg.get("main"),
        "user_branch": cfg.get("user_branch"),
        "current_branch": cur,
        "ahead": ahead,
        "behind": behind,
        "dirty_files": dirty_count,
        "last_commit": last_commit.strip(),
    }
    if not upstream:
        status_obj["upstream"] = None
        status_obj["set_upstream_hint"] = "git push -u origin HEAD"
    else:
        status_obj["upstream"] = upstream
    print(json.dumps(status_obj, indent=2))
    print("— git status —")
    run(["git", "status", "-sb"])

def cmd_pull():
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    cur = current_branch()
    
    # Check for uncommitted changes and offer save/stash
    rc, out = run(["git", "status", "--porcelain"], check=False)
    stashed = False
    if out.strip():
        print("⚠️  You have uncommitted changes:")
        print(out)
        print("\nWhat would you like to do?")
        print("1. Save changes (commit now)")
        print("2. Stash and re-apply after update")
        print("3. Cancel pull")
        response = input("Enter 1, 2, or 3: ")
        if response == "1":
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_all(f"mel save @ {ts}", root)
        elif response == "2":
            print("Stashing and will re-apply after update...")
            run(["git", "stash", "push", "-m", "mel pull temp"])
            stashed = True
        elif response == "3":
            print("Pull cancelled.")
            sys.exit(0)
        else:
            print("Invalid choice. Pull cancelled.")
            sys.exit(1)
    
    # Now pull the latest changes from main
    fetch_origin()
    base_ref = f"origin/{main}" if has_remote("origin") else main
    
    if cur == main:
        # On main branch, just pull
        if has_remote("origin"):
            run(["git", "pull", "--ff-only", "origin", main])
        print("✓ Updated main to latest.")
    else:
        # On feature branch, update with latest main via configured strategy
        strategy = (cfg.get("update_strategy") or "rebase").lower()
        print(f"📥 Updating current branch with latest {main} via {strategy}...")
        if strategy == "merge":
            msg = format_merge_message(cfg, "update", cur, main)
            try:
                if msg:
                    run(["git", "merge", "--no-edit", "-m", msg, base_ref])
                else:
                    run(["git", "merge", base_ref])
            except subprocess.CalledProcessError:
                print("✖ Merge hit conflicts. Fix files → git add -A && git merge --continue, or git merge --abort.")
                sys.exit(2)
        else:
            rebase_onto(base_ref)
        if stashed:
            print("Re-applying stashed changes...")
            rc, _ = run(["git", "stash", "pop"], check=False)
            if rc != 0:
                print("⚠️  Conflicts may have occurred while applying stashed changes. Resolve and continue.")
        print("✓ Updated feature branch with latest main.")

 

def cmd_update():
    cmd_pull()

def cmd_diff():
    print("— Diff (staged) —")
    run(["git", "diff", "--staged", "--stat"], check=False)
    print("\n— Diff (unstaged) —")
    run(["git", "diff", "--stat"], check=False)

def cmd_open(target=None):
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    base = get_origin_web_url()
    if not base:
        print("! Cannot determine origin URL.")
        sys.exit(1)
    # Simplified: always open repo homepage
    url = base
    print(f"→ Opening {url}")
    open_url(url)

def cmd_pr():
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    base = get_origin_web_url()
    if not base:
        print("! Cannot determine origin URL.")
        sys.exit(1)
    cur = current_branch()
    if "github.com" in base:
        url = f"{base}/compare/{main}...{cur}?expand=1"
    else:
        url = base
    print(f"→ Opening PR: {url}")
    open_url(url)

def cmd_version():
    path = os.path.realpath(sys.argv[0])
    print(f"mel {VERSION}")
    print(f"path: {path}")

def check_for_updates_silently():
    """Check for updates silently and upgrade if available. Returns True if upgrade was performed."""
    try:
        # Get latest release info from GitHub API
        url = "https://api.github.com/repos/davefowler/melcurial/releases/latest"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data["tag_name"].lstrip("v")  # Remove 'v' prefix if present
            download_url = None
            
            # Find the mel script in the release assets
            for asset in data.get("assets", []):
                if asset["name"] == "mel":
                    download_url = asset["browser_download_url"]
                    break
            
            if not download_url:
                return False
            
            # Compare versions (simple string comparison should work for semantic versions)
            if latest_version <= VERSION:
                return False
            
            # Silent upgrade - no user interaction needed
            current_path = os.path.realpath(sys.argv[0])
            
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mel') as temp_file:
                temp_path = temp_file.name
            
            try:
                # Download the new version
                with urllib.request.urlopen(download_url, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    with open(temp_path, 'w') as f:
                        f.write(content)
                
                # Make it executable
                os.chmod(temp_path, 0o755)
                
                # Backup current version
                backup_path = current_path + ".backup"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(current_path, backup_path)
                
                # Install new version
                os.rename(temp_path, current_path)
                
                print(f"🔄 mel updated to v{latest_version} (was v{VERSION})")
                return True
                
            except Exception as e:
                # Restore backup if something went wrong
                if os.path.exists(backup_path) and not os.path.exists(current_path):
                    os.rename(backup_path, current_path)
                return False
            finally:
                # Clean up temp file if it still exists
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except Exception:
        # Silently fail - don't interrupt user's workflow
        return False

def should_check_for_updates():
    """Determine if we should check for updates based on last check time and random chance."""
    try:
        # Check if we're in a git repo (don't auto-update in non-git contexts)
        repo_root()
    except:
        return False
    
    # Get config to check last update time
    try:
        root = repo_root()
        cfg = load_config(root)
        last_check = cfg.get("last_update_check", 0)
        current_time = datetime.datetime.now().timestamp()
        
        # Check every 24 hours (86400 seconds)
        if current_time - last_check < 86400:
            return False
        
        # Also add some randomness - only check 1 in 3 times even after 24 hours
        import random
        if random.randint(1, 3) != 1:
            return False
        
        return True
    except:
        return False

def update_last_check_time():
    """Update the last check time in config."""
    try:
        root = repo_root()
        cfg = load_config(root)
        cfg["last_update_check"] = datetime.datetime.now().timestamp()
        save_config(root, cfg)
    except:
        pass

def cmd_upgrade():
    """Manual upgrade command - same as before but with user interaction."""
    print("🔍 Checking for latest version...")
    
    try:
        # Get latest release info from GitHub API
        url = "https://api.github.com/repos/davefowler/melcurial/releases/latest"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            latest_version = data["tag_name"].lstrip("v")  # Remove 'v' prefix if present
            download_url = None
            
            # Find the mel script in the release assets
            for asset in data.get("assets", []):
                if asset["name"] == "mel":
                    download_url = asset["browser_download_url"]
                    break
            
            if not download_url:
                print("✖ Could not find mel script in latest release assets.")
                sys.exit(1)
            
            print(f"📦 Latest version: {latest_version}")
            print(f"📦 Current version: {VERSION}")
            
            # Compare versions (simple string comparison should work for semantic versions)
            if latest_version == VERSION:
                print("✓ You're already running the latest version!")
                return
            
            if latest_version < VERSION:
                print("⚠️  You're running a newer version than what's available on GitHub.")
                print("   This might be a development build.")
                return
            
            # Ask for confirmation
            print(f"\n🔄 Upgrade from {VERSION} to {latest_version}?")
            response = input("Type 'y' to continue, anything else to abort: ")
            if response.lower() != 'y':
                print("Upgrade cancelled.")
                return
            
            # Download and install the new version
            print("📥 Downloading latest version...")
            current_path = os.path.realpath(sys.argv[0])
            
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mel') as temp_file:
                temp_path = temp_file.name
            
            try:
                # Download the new version
                with urllib.request.urlopen(download_url) as response:
                    content = response.read().decode('utf-8')
                    with open(temp_path, 'w') as f:
                        f.write(content)
                
                # Make it executable
                os.chmod(temp_path, 0o755)
                
                # Backup current version
                backup_path = current_path + ".backup"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(current_path, backup_path)
                
                # Install new version
                os.rename(temp_path, current_path)
                
                print("✓ Upgrade complete!")
                print(f"✓ Installed mel {latest_version}")
                print(f"✓ Previous version backed up to: {backup_path}")
                print("\n💡 You may need to restart your terminal or run 'hash -r' to use the new version.")
                
            except Exception as e:
                # Restore backup if something went wrong
                if os.path.exists(backup_path) and not os.path.exists(current_path):
                    os.rename(backup_path, current_path)
                    print(f"✖ Upgrade failed: {e}")
                    print("✓ Restored previous version.")
                else:
                    print(f"✖ Upgrade failed: {e}")
                sys.exit(1)
            finally:
                # Clean up temp file if it still exists
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except urllib.error.URLError as e:
        print(f"✖ Failed to check for updates: {e}")
        print("   Make sure you have an internet connection.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✖ Failed to parse release information: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✖ Unexpected error during upgrade: {e}")
        sys.exit(1)

def ensure_clean_or_handle(non_interactive=False):
    rc, out = run(["git", "status", "--porcelain"], check=False)
    if not out.strip():
        return "clean"
    print("⚠️  You have uncommitted changes:")
    print(out)
    if non_interactive:
        print("--yes provided. Defaulting to 'Save changes'.")
        return "save"
    print("\nWhat would you like to do?")
    print("1. Save changes (commit now)")
    print("2. Stash and re-apply after update")
    print("3. Cancel")
    response = input("Enter 1, 2, or 3: ")
    if response == "1":
        return "save"
    elif response == "2":
        return "stash"
    elif response == "3":
        print("Cancelled.")
        sys.exit(0)
    else:
        print("Invalid choice. Cancelled.")
        sys.exit(1)

def cmd_sync(non_interactive=False):
    root = repo_root()
    cfg = get_cfg(root)
    main = cfg["main"]
    cur = current_branch()

    if cur == main:
        print(f"✖ You’re on '{main}'. Create your workspace branch first (e.g. 'git checkout -b <name>').")
        sys.exit(1)

    action = ensure_clean_or_handle(non_interactive=non_interactive)
    stashed = False
    if action == "save":
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_all(f"mel save @ {ts}", root)
    elif action == "stash":
        print("Stashing changes for sync...")
        run(["git", "stash", "push", "-m", "mel sync temp"])
        stashed = True

    fetch_origin()
    base_ref = f"origin/{main}" if has_remote("origin") else main

    strategy = (cfg.get("update_strategy") or "rebase").lower()
    print(f"🔄 Sync: updating {cur} with latest {main} via {strategy}...")
    if strategy == "merge":
        msg = format_merge_message(cfg, "sync", cur, main)
        try:
            if msg:
                run(["git", "merge", "--no-edit", "-m", msg, base_ref])
            else:
                run(["git", "merge", base_ref])
        except subprocess.CalledProcessError:
            print("✖ Merge hit conflicts. Fix files → git add -A && git merge --continue, or git merge --abort.")
            sys.exit(2)
    else:
        rebase_onto(base_ref)

    if stashed:
        print("Re-applying stashed changes...")
        rc, _ = run(["git", "stash", "pop"], check=False)
        if rc != 0:
            print("⚠️  Conflicts may have occurred while applying stashed changes. Resolve, then 'git add -A' and continue.")

    push_current(set_upstream=False)

    base = get_origin_web_url()
    if base and cfg.get("open_pr_on_sync"):
        if "github.com" in base:
            pr_url = f"{base}/compare/{main}...{cur}?expand=1"
            print(f"→ Opening PR: {pr_url}")
            open_url(pr_url)
        else:
            print("! open_pr_on_sync configured, but could not determine PR URL for this remote.")
    print("✓ Sync complete.")

def cmd_mode(mode=None):
    root = repo_root()
    cfg = get_cfg(root)
    
    if not mode:
        current_mode = cfg.get("contributor_mode", "basic")
        print(f"Current mode: {current_mode}")
        print("Use 'mel mode basic' or 'mel mode advanced' to change")
        return
    
    mode = mode.lower()
    if mode not in ["basic", "advanced"]:
        print("✖ Mode must be 'basic' or 'advanced'")
        sys.exit(1)
    
    cfg["contributor_mode"] = mode
    save_config(root, cfg)
    print(f"✓ Switched to {mode} mode")

def cmd_help():
    root = repo_root()
    cfg = get_cfg(root)
    configured = cfg.get("scripts") or {}
    package = load_package_scripts(root) if cfg.get("allow_package_scripts") else {}
    
    scripts_section = ""
    if configured or package:
        scripts_section = "\nScripts:\n"
        if configured:
            for k, v in configured.items():
                if isinstance(v, str):
                    display = v
                elif isinstance(v, dict):
                    display = v.get("description") or v.get("cmd", "")
                else:
                    display = ""
                scripts_section += f"  mel {k}        {display}\n"
        if package:
            for k, v in sorted(package.items()):
                scripts_section += f"  mel {k}        {v}\n"

    mode = (cfg.get("contributor_mode") or "basic").lower()

    if mode == "basic":
        help_text = HELP_HEADER + "\n" + HELP_BASIC + HELP_FOOTER + scripts_section
    else:
        help_text = HELP_HEADER + "\n" + HELP_BASIC + HELP_ADVANCED + HELP_FOOTER + scripts_section
    print(help_text.strip())

def cmd_scripts():
    root = repo_root()
    cfg = get_cfg(root)
    configured = cfg.get("scripts") or {}
    package = load_package_scripts(root) if cfg.get("allow_package_scripts") else {}
    printed = False
    if configured:
        print("— Configured scripts (.mel/config.json) —")
        for k, v in configured.items():
            if isinstance(v, str):
                print(f"{k}: {v}")
            elif isinstance(v, dict):
                print(f"{k}: {v.get('cmd','')}")
            else:
                print(f"{k}: (unsupported)")
        printed = True
    if package:
        if printed:
            print()
        print("— Package scripts (package.json) —")
        for k, v in sorted(package.items()):
            print(f"{k}: {v}")
        printed = True
    if not printed:
        print("(no scripts available)")

def auto_init_if_needed():
    # Ensure a repo exists and config is present; if missing, prompt and create branch + config
    root = repo_root()
    cfg_path = os.path.join(root, CONFIG_DIRNAME, CONFIG_FILENAME)
    if os.path.exists(cfg_path):
        return
    print("It looks like this is your first time using mel in this repo.")
    entered = input("What's your name? We'll create a branch with it: ").strip()
    if not entered:
        print("✖ No name provided.")
        sys.exit(1)
    branch = sanitize_branch_name(entered)
    try:
        cmd_start(branch)
    except subprocess.CalledProcessError as e:
        print(f"\n✖ Failed to initialize mel in this repository:")
        print(f"  {e}")
        print("\nThis usually happens when you have uncommitted changes.")
        print("To fix this, you can:")
        print("  • Run 'mel clear' to stash your changes, then try again")
        print("  • Or commit your changes first with 'git add -A && git commit -m \"your message\"'")
        print("  • Or manually resolve any conflicts and try again")
        sys.exit(1)

def main():
    # Check for automatic updates (only for certain commands to avoid interrupting workflow)
    if len(sys.argv) >= 2:
        cmd = sys.argv[1]
        # Only auto-update for common workflow commands, not for help/version/upgrade itself
        if cmd in ["save", "status", "publish", "reset", "b", "branch", "clear", "pull", "update", "sync"]:
            if should_check_for_updates():
                update_last_check_time()  # Update timestamp even if check fails
                if check_for_updates_silently():
                    # If we upgraded, restart with the new version
                    import subprocess
                    subprocess.run([sys.executable] + sys.argv)
                    sys.exit(0)
    
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)
    yes_mode = (os.environ.get("MEL_YES") == "1" or "--yes" in sys.argv)
    args = [a for a in sys.argv[1:] if a != "--yes"]
    cmd = args[0]
    if cmd in ("help", "-h", "--help"):
        cmd_help()
    elif cmd in ("--version", "-v"):
        cmd_version()
    elif cmd == "save":
        auto_init_if_needed()
        msg = args[1] if len(args) >= 2 else None
        cmd_save(msg)
    elif cmd == "deploy":
        auto_init_if_needed()
        cmd_deploy()
    elif cmd == "publish":
        auto_init_if_needed()
        cmd_publish()
    elif cmd == "freshstart":
        auto_init_if_needed()
        cmd_freshstart()
    elif cmd == "reset":
        auto_init_if_needed()
        cmd_reset()
    elif cmd in ("b", "branch"):
        auto_init_if_needed()
        if len(args) >= 2:
            cmd_b(args[1])
        else:
            print("Usage: mel b <branch> | mel branch <branch>")
            sys.exit(1)
    elif cmd == "clear":
        auto_init_if_needed()
        cmd_clear()
    elif cmd == "status":
        auto_init_if_needed()
        cmd_status()
    elif cmd == "pull":
        auto_init_if_needed()
        cmd_pull()
    elif cmd == "update":
        auto_init_if_needed()
        cmd_update()
    
    elif cmd == "sync":
        auto_init_if_needed()
        cmd_sync(non_interactive=yes_mode)
    elif cmd == "open":
        auto_init_if_needed()
        cmd_open()
    elif cmd == "pr":
        auto_init_if_needed()
        cmd_pr()
    elif cmd == "diff":
        auto_init_if_needed()
        cmd_diff()
    elif cmd == "mode":
        auto_init_if_needed()
        mode_arg = args[1] if len(args) >= 2 else None
        cmd_mode(mode_arg)
    elif cmd == "scripts":
        auto_init_if_needed()
        cmd_scripts()
    elif cmd == "upgrade":
        cmd_upgrade()
    
    else:
        # Prevent unknown flags from being treated as script names
        if cmd.startswith("-"):
            print(f"✖ Unknown flag: {cmd}\nUse 'mel --help' for usage.")
            sys.exit(1)
        
        # Check for configured scripts
        try:
            root = repo_root()
            cfg = get_cfg(root)
        except Exception:
            cfg = {"scripts": {}, "allow_package_scripts": False}
        configured_scripts = (cfg.get("scripts") or {})
        if cmd in configured_scripts:
            # Collect extra args (support both "-- args" and direct args)
            if "--" in args:
                idx = args.index("--")
                extra = args[idx+1:]
            else:
                extra = args[1:]
            rc = run_script_by_name(cfg, cmd, extra)
            sys.exit(rc)
        
        # Fallback: treat unknown command as a script name
        name = cmd
        # Collect extra args (support both "-- args" and direct args)
        extra = []
        if "--" in args:
            idx = args.index("--")
            extra = args[idx+1:]
        else:
            extra = args[1:]
        rc = run_script_by_name(cfg, name, extra)
        sys.exit(rc)

if __name__ == "__main__":
    main()