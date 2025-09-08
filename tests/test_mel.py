import importlib.util
from importlib.machinery import SourceFileLoader
import pathlib
import types
import pytest
import os
import json
import subprocess


def load_mel_module() -> types.ModuleType:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    mel_path = repo_root / "mel"
    # Use SourceFileLoader to handle files without .py extension
    loader = SourceFileLoader("mel_module", str(mel_path))
    module = types.ModuleType(loader.name)
    loader.exec_module(module)
    return module


def test_sanitize_branch_name_basic_cases():
    mel = load_mel_module()
    assert mel.sanitize_branch_name("Feature New Landing") == "feature-new-landing"
    assert mel.sanitize_branch_name("Weird@@Name!!") == "weird-name"
    assert mel.sanitize_branch_name("a.b/c_d-1") == "a.b/c_d-1"


def test_sanitize_branch_name_head_and_blank():
    mel = load_mel_module()
    assert mel.sanitize_branch_name("   ").startswith("mel-")
    assert mel.sanitize_branch_name("HEAD").startswith("mel-")


def test_get_origin_web_url_parses_ssh_and_https(monkeypatch):
    mel = load_mel_module()

    def fake_run_ssh(cmd, check=False):  # type: ignore[unused-argument]
        return 0, "git@github.com:owner/repo.git\n"

    monkeypatch.setattr(mel, "run", fake_run_ssh)
    assert mel.get_origin_web_url() == "https://github.com/owner/repo"

    def fake_run_https(cmd, check=False):  # type: ignore[unused-argument]
        return 0, "https://github.com/owner/repo.git\n"

    monkeypatch.setattr(mel, "run", fake_run_https)
    assert mel.get_origin_web_url() == "https://github.com/owner/repo"

    def fake_run_empty(cmd, check=False):  # type: ignore[unused-argument]
        return 0, "\n"

    monkeypatch.setattr(mel, "run", fake_run_empty)
    assert mel.get_origin_web_url() is None


def test_detect_package_manager(tmp_path, monkeypatch):
    mel = load_mel_module()

    # Default when nothing present - should return None
    monkeypatch.chdir(tmp_path)
    assert mel.detect_package_manager(tmp_path.as_posix()) is None

    # yarn
    (tmp_path / "yarn.lock").write_text("")
    assert mel.detect_package_manager(tmp_path.as_posix()) == "yarn"

    # pnpm has priority over yarn
    (tmp_path / "pnpm-lock.yaml").write_text("")
    assert mel.detect_package_manager(tmp_path.as_posix()) == "pnpm"


def test_run_script_by_name_from_config_success(tmp_path, monkeypatch):
    mel = load_mel_module()

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text(
        '{"main":"main","scripts":{"test":"cmd_test"}}'
    )

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    calls = []

    def fake_run(cmd, check=False, cwd=None, env=None):  # type: ignore[unused-argument]
        calls.append(cmd)
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    cfg = mel.get_cfg(tmp_path.as_posix())
    rc = mel.run_script_by_name(cfg, "test", extra_args=[])
    assert rc == 0
    assert calls == ["cmd_test"]


def test_run_script_by_name_from_config_failure(tmp_path, monkeypatch):
    mel = load_mel_module()

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text(
        '{"main":"main","scripts":{"test":"fail"}}'
    )

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    def fake_run(cmd, check=False, cwd=None, env=None):  # type: ignore[unused-argument]
        if cmd == "fail":
            return 1, "boom"
        return 0, "ok"

    monkeypatch.setattr(mel, "run", fake_run)

    cfg = mel.get_cfg(tmp_path.as_posix())
    rc = mel.run_script_by_name(cfg, "test", extra_args=[])
    assert rc == 1


def test_run_script_falls_back_to_package_manager(tmp_path, monkeypatch):
    mel = load_mel_module()

    # Prepare repo root with package.json (no local scripts config for target)
    (tmp_path / "package.json").write_text('{"name":"x","scripts":{"build":"echo hi"}}')
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main","allow_package_scripts":true}')

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    # Ensure default package manager selection is used (npm)

    calls = []

    def fake_run(cmd, check=False, cwd=None, env=None):  # type: ignore[unused-argument]
        calls.append(cmd)
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    cfg = mel.get_cfg(tmp_path.as_posix())
    rc = mel.run_script_by_name(cfg, "build", extra_args=["--flag"]) 
    assert rc == 0
    assert calls == ["npm run build -- --flag"]


def test_format_merge_message(monkeypatch):
    mel = load_mel_module()

    monkeypatch.setattr(mel, "get_current_author", lambda: "Alice")

    cfg = {
        "merge_message": "Merge {branch} into {main} by {author} @ {datetime}",
    }
    msg = mel.format_merge_message(cfg, "update", "feature/foo", "main")
    assert "feature/foo" in msg
    assert "main" in msg
    assert "Alice" in msg


def test_ensure_mel_gitignored_appends_once(tmp_path):
    mel = load_mel_module()
    gi = tmp_path / ".gitignore"
    gi.write_text("node_modules/\n# comment\n")
    mel.ensure_mel_gitignored(tmp_path.as_posix())
    content = gi.read_text()
    assert ".mel/" in content
    before = content
    # Calling again should be idempotent
    mel.ensure_mel_gitignored(tmp_path.as_posix())
    assert gi.read_text() == before


def test_import_repo_template_creates_config_and_gitignore(tmp_path, monkeypatch):
    mel = load_mel_module()
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config_template.json").write_text('{"scripts": {"test": "echo hi"}}')

    # Prepare .gitignore
    (tmp_path / ".gitignore").write_text("# ignore\n")

    cfg = mel.get_cfg(tmp_path.as_posix())
    assert cfg.get("scripts", {}).get("test") == "echo hi"
    # Config file should be created from template
    assert (mel_dir / "config.json").exists()
    # .gitignore should be updated
    assert ".mel/" in (tmp_path / ".gitignore").read_text()





def test_open_runs_without_engineer_mode(tmp_path, monkeypatch):
    mel = load_mel_module()
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main"}')

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "current_branch", lambda: "feature/x")
    monkeypatch.setattr(mel, "get_origin_web_url", lambda: "https://github.com/owner/repo")
    # Avoid actually opening the browser
    opened = {"url": None}
    monkeypatch.setattr(mel, "open_url", lambda url: opened.update({"url": url}))

    mel.cmd_open()
    assert opened["url"] == "https://github.com/owner/repo"



def test_start_creates_config_when_missing(tmp_path, monkeypatch):
    mel = load_mel_module()

    # No template present, no config present
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()

    # Use the temp path as repo root and avoid real git
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)

    calls = []

    def fake_run(cmd, check=True, cwd=None, env=None):  # type: ignore[unused-argument]
        calls.append(cmd)
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    # Run start, which should materialize a config.json via get_cfg/save_config
    mel.cmd_start("feature/test-start-config")

    cfg_path = mel_dir / "config.json"
    assert cfg_path.exists()
    cfg = (cfg_path).read_text()
    # Should include at least defaults like main and update_strategy
    assert '"main"' in cfg
    assert '"update_strategy"' in cfg


def test_start_uses_repo_template_if_available(tmp_path, monkeypatch):
    mel = load_mel_module()

    # Provide a repo-local template
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config_template.json").write_text('{"scripts": {"test": "echo hi"}}')

    # Prepare .gitignore to verify it stays valid, though not required
    (tmp_path / ".gitignore").write_text("# ignore\n")

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)

    def fake_run(cmd, check=True, cwd=None, env=None):  # type: ignore[unused-argument]
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    mel.cmd_start("feature/with-template")

    cfg_path = mel_dir / "config.json"
    assert cfg_path.exists()
    cfg_text = cfg_path.read_text()
    assert '"scripts"' in cfg_text and '"test"' in cfg_text and '"echo hi"' in cfg_text


def test_help_basic_mode_shows_basic_only(tmp_path, monkeypatch, capsys):
    mel = load_mel_module()

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    # contributor_mode basic should hide Advanced section
    (mel_dir / "config.json").write_text(
        '{"main":"main","contributor_mode":"basic"}'
    )

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    mel.cmd_help()
    out = capsys.readouterr().out
    assert "Basic commands:" in out
    assert "Advanced commands:" not in out
    assert "mel reset" in out
    assert "mel diff" not in out
    assert "mel update" not in out


def test_help_advanced_mode_shows_advanced(tmp_path, monkeypatch, capsys):
    mel = load_mel_module()

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    # contributor_mode advanced should include Advanced section
    (mel_dir / "config.json").write_text(
        '{"main":"main","contributor_mode":"advanced"}'
    )

    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    mel.cmd_help()
    out = capsys.readouterr().out
    assert "Basic commands:" in out
    assert "Advanced commands:" in out
    assert "mel reset" in out
    assert "mel diff" in out


def test_script_execution_works(tmp_path, monkeypatch):
    mel = load_mel_module()

    # Configure a custom script
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text(
        '{"main":"main","scripts":{"custom":"echo hello"}}'
    )

    # Use temp path as repo root; avoid real git calls
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    calls = []

    def fake_run(cmd, check=False, cwd=None, env=None):  # type: ignore[unused-argument]
        calls.append(cmd)
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    # Simulate CLI invocation: `mel custom`
    monkeypatch.setattr(mel.sys, "argv", ["mel", "custom"]) 
    monkeypatch.setenv("MEL_YES", "1")

    with pytest.raises(SystemExit) as e:
        mel.main()

    # Should exit successfully and have run the configured script
    assert e.value.code == 0
    assert calls == ["echo hello"]


def test_auto_init_creates_config_at_git_root_from_subdir(tmp_path, monkeypatch):
    mel = load_mel_module()

    nested = tmp_path / "nested" / "deep"
    nested.mkdir(parents=True)

    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()

    monkeypatch.chdir(nested)

    def fake_run(cmd, check=True, cwd=None, env=None):  # type: ignore[unused-argument]
        if isinstance(cmd, list) and cmd[:3] == ["git", "rev-parse", "--show-toplevel"]:
            return 0, tmp_path.as_posix() + "\n"
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    # input is a builtin, so patch builtins.input
    import builtins as _builtins
    monkeypatch.setattr(_builtins, "input", lambda prompt="": "Alice Example")

    mel.auto_init_if_needed()

    cfg_path = tmp_path / ".mel" / "config.json"
    assert cfg_path.exists()
    assert not (nested / ".mel" / "config.json").exists()


def test_repo_root_is_used_even_when_called_in_subdir(tmp_path, monkeypatch):
    mel = load_mel_module()

    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (tmp_path / ".mel").mkdir()

    monkeypatch.chdir(nested)

    calls = []

    def fake_run(cmd, check=True, cwd=None, env=None):  # type: ignore[unused-argument]
        calls.append(cmd)
        if isinstance(cmd, list) and cmd[:3] == ["git", "rev-parse", "--show-toplevel"]:
            return 0, tmp_path.as_posix() + "\n"
        return 0, ""

    monkeypatch.setattr(mel, "run", fake_run)

    root = mel.repo_root()
    assert root == tmp_path.as_posix()
    assert any(isinstance(c, list) and c[:3] == ["git", "rev-parse", "--show-toplevel"] for c in calls)


def test_uses_repo_root_for_config_and_template(tmp_path, monkeypatch):
    """Test that mel finds repo root and uses config template from there, 
    and creates config in repo root even when called from subdirectory."""
    mel = load_mel_module()
    
    # Create repo structure with template in repo root
    repo_root = tmp_path / "my-repo"
    repo_root.mkdir()
    subdir = repo_root / "subdir"
    subdir.mkdir()
    
    # Create template in repo root
    mel_dir = repo_root / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config_template.json").write_text('{"scripts": {"test": "echo from repo root"}}')
    
    # Mock git to return the repo root
    monkeypatch.setattr(mel, "repo_root", lambda: str(repo_root))
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    def fake_run(cmd, check=True, cwd=None, env=None):  # type: ignore[unused-argument]
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Simulate running mel from subdirectory
    # Change working directory to subdir
    original_cwd = os.getcwd()
    try:
        os.chdir(str(subdir))
        
        # Call get_cfg which should find the template in repo root
        cfg = mel.get_cfg(str(repo_root))
        
        # Verify template was used
        assert cfg.get("scripts", {}).get("test") == "echo from repo root"
        
        # Verify config was created in repo root, not subdir
        repo_config_path = repo_root / ".mel" / "config.json"
        subdir_config_path = subdir / ".mel" / "config.json"
        
        assert repo_config_path.exists(), "Config should be created in repo root"
        assert not subdir_config_path.exists(), "Config should not be created in subdirectory"
        
        # Verify config content
        with open(repo_config_path, "r") as f:
            config_content = json.load(f)
        assert config_content.get("scripts", {}).get("test") == "echo from repo root"
        
    finally:
        os.chdir(original_cwd)


def test_cmd_start_handles_uncommitted_changes(tmp_path, monkeypatch, capsys):
    """Test that cmd_start properly handles uncommitted changes by offering options."""
    mel = load_mel_module()
    
    # Set up a mock repo
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main"}')
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    # Mock git status to return uncommitted changes
    def fake_run(cmd, check=True, cwd=None, env=None):
        if isinstance(cmd, list) and cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            return 0, " M modified_file.txt\n?? new_file.txt\n"
        elif isinstance(cmd, list) and cmd[:2] == ["git", "checkout"]:
            # This should not be called if we handle uncommitted changes properly
            raise subprocess.CalledProcessError(1, cmd, "error: Your local changes would be overwritten")
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Mock input to simulate user choosing to stash changes
    import builtins as _builtins
    monkeypatch.setattr(_builtins, "input", lambda prompt="": "2")
    
    # Mock the stash command and successful checkout after stashing
    stash_calls = []
    checkout_calls = []
    def fake_run_with_stash(cmd, check=True, cwd=None, env=None):
        if isinstance(cmd, list) and cmd[:2] == ["git", "stash"]:
            stash_calls.append(cmd)
            return 0, ""
        elif isinstance(cmd, list) and cmd[:2] == ["git", "checkout"]:
            checkout_calls.append(cmd)
            return 0, ""
        return fake_run(cmd, check, cwd, env)
    
    monkeypatch.setattr(mel, "run", fake_run_with_stash)
    
    # This should not raise an exception
    mel.cmd_start("test-branch")
    
    # Verify that stash was called
    assert len(stash_calls) > 0
    assert any("stash" in " ".join(cmd) for cmd in stash_calls)
    
    # Verify that checkout was called after stashing
    assert len(checkout_calls) > 0
    assert any("checkout" in " ".join(cmd) for cmd in checkout_calls)
    
    # Verify the output shows the uncommitted changes
    out = capsys.readouterr().out
    assert "⚠️  You have uncommitted changes:" in out
    assert "modified_file.txt" in out
    assert "new_file.txt" in out
    assert "Stashing changes..." in out
    assert "✓ Changes stashed" in out


def test_cmd_start_handles_uncommitted_changes_commit_option(tmp_path, monkeypatch, capsys):
    """Test that cmd_start can commit changes when user chooses option 1."""
    mel = load_mel_module()
    
    # Set up a mock repo
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main"}')
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    commit_calls = []
    checkout_calls = []
    
    def fake_run(cmd, check=True, cwd=None, env=None):
        if isinstance(cmd, list) and cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            return 0, " M modified_file.txt\n"
        elif isinstance(cmd, list) and cmd[:2] == ["git", "add"]:
            commit_calls.append(cmd)
            return 0, ""
        elif isinstance(cmd, list) and cmd[:2] == ["git", "commit"]:
            commit_calls.append(cmd)
            return 0, ""
        elif isinstance(cmd, list) and cmd[:2] == ["git", "checkout"]:
            checkout_calls.append(cmd)
            return 0, ""
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Mock input to simulate user choosing to commit changes and confirming file addition
    import builtins as _builtins
    input_responses = ["1", "y"]  # First for branch creation choice, second for file confirmation
    input_call_count = 0
    def mock_input(prompt=""):
        nonlocal input_call_count
        response = input_responses[input_call_count]
        input_call_count += 1
        return response
    monkeypatch.setattr(_builtins, "input", mock_input)
    
    # This should not raise an exception
    mel.cmd_start("test-branch")
    
    # Verify that commit was called
    assert len(commit_calls) > 0
    assert any("add" in " ".join(cmd) for cmd in commit_calls)
    assert any("commit" in " ".join(cmd) for cmd in commit_calls)
    
    # Verify checkout was called after committing
    assert len(checkout_calls) > 0


def test_cmd_start_handles_uncommitted_changes_cancel_option(tmp_path, monkeypatch, capsys):
    """Test that cmd_start exits when user chooses to cancel."""
    mel = load_mel_module()
    
    # Set up a mock repo
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main"}')
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    def fake_run(cmd, check=True, cwd=None, env=None):
        if isinstance(cmd, list) and cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            return 0, " M modified_file.txt\n"
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Mock input to simulate user choosing to cancel
    import builtins as _builtins
    monkeypatch.setattr(_builtins, "input", lambda prompt="": "3")
    
    # This should exit with code 0
    with pytest.raises(SystemExit) as e:
        mel.cmd_start("test-branch")
    assert e.value.code == 0
    
    # Verify the output shows cancellation message
    out = capsys.readouterr().out
    assert "Branch creation cancelled." in out


def test_auto_init_if_needed_handles_git_errors_gracefully(tmp_path, monkeypatch, capsys):
    """Test that auto_init_if_needed provides helpful error messages when git operations fail."""
    mel = load_mel_module()
    
    # Set up a mock repo without config
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    # Mock input to provide a name
    import builtins as _builtins
    monkeypatch.setattr(_builtins, "input", lambda prompt="": "testuser")
    
    # Mock cmd_start to raise an exception
    def fake_cmd_start(branch_name):
        raise subprocess.CalledProcessError(1, ["git", "checkout"], "error: Your local changes would be overwritten")
    
    monkeypatch.setattr(mel, "cmd_start", fake_cmd_start)
    
    # This should exit with code 1 and show helpful error message
    with pytest.raises(SystemExit) as e:
        mel.auto_init_if_needed()
    assert e.value.code == 1
    
    # Verify the output shows helpful error message
    out = capsys.readouterr().out
    assert "✖ Failed to initialize mel in this repository:" in out
    assert "This usually happens when you have uncommitted changes." in out
    assert "mel clear" in out


def test_auto_init_asks_for_name_and_creates_branch(tmp_path, monkeypatch, capsys):
    """Test that auto_init_if_needed asks for name and creates branch."""
    mel = load_mel_module()
    
    # Set up a mock repo without config
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    # Mock input to provide a name
    import builtins as _builtins
    monkeypatch.setattr(_builtins, "input", lambda prompt="": "testuser")
    
    # Mock cmd_start to avoid actual git operations
    def fake_cmd_start(branch_name):
        print(f"✓ Now on '{branch_name}' (based on main).")
    
    monkeypatch.setattr(mel, "cmd_start", fake_cmd_start)
    
    # This should ask for input and create a branch
    mel.auto_init_if_needed()
    
    # Verify the output shows the expected behavior
    out = capsys.readouterr().out
    assert "It looks like this is your first time using mel in this repo." in out
    assert "✓ Now on 'testuser' (based on main)." in out


def test_mel_works_without_package_json(tmp_path, monkeypatch, capsys):
    """Test that mel works correctly in a Python project without package.json."""
    mel = load_mel_module()
    
    # Set up a Python project (no package.json)
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main","allow_package_scripts":false}')
    
    # Create some Python files to make it look like a Python project
    (tmp_path / "main.py").write_text("print('Hello, World!')")
    (tmp_path / "requirements.txt").write_text("requests==2.28.0")
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    # Mock git commands
    def fake_run(cmd, check=True, cwd=None, env=None):
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Test help command - should not show package scripts
    mel.cmd_help()
    out = capsys.readouterr().out
    assert "Package scripts" not in out
    assert "package.json" not in out
    
    # Test scripts command - should not show package scripts
    mel.cmd_scripts()
    out = capsys.readouterr().out
    assert "Package scripts" not in out
    assert "package.json" not in out
    assert "(no scripts available)" in out


def test_mel_works_with_package_json_when_enabled(tmp_path, monkeypatch, capsys):
    """Test that mel works with package.json when allow_package_scripts is enabled."""
    mel = load_mel_module()
    
    # Set up a Node.js project with package.json
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main","allow_package_scripts":true}')
    
    # Create package.json
    (tmp_path / "package.json").write_text('{"scripts":{"test":"jest","build":"webpack"}}')
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    monkeypatch.setattr(mel, "has_remote", lambda remote="origin": False)
    
    # Mock git commands
    def fake_run(cmd, check=True, cwd=None, env=None):
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    # Test help command - should show package scripts
    mel.cmd_help()
    out = capsys.readouterr().out
    assert "mel test" in out
    assert "mel build" in out
    
    # Test scripts command - should show package scripts
    mel.cmd_scripts()
    out = capsys.readouterr().out
    assert "Package scripts (package.json)" in out
    assert "test: jest" in out
    assert "build: webpack" in out


def test_detect_package_manager_returns_none_for_python_project(tmp_path, monkeypatch):
    """Test that detect_package_manager returns None for Python projects."""
    mel = load_mel_module()
    
    # Create a Python project (no package.json, yarn.lock, or pnpm-lock.yaml)
    (tmp_path / "main.py").write_text("print('Hello, World!')")
    (tmp_path / "requirements.txt").write_text("requests==2.28.0")
    
    result = mel.detect_package_manager(tmp_path.as_posix())
    assert result is None


def test_detect_package_manager_detects_npm(tmp_path, monkeypatch):
    """Test that detect_package_manager detects npm when package.json exists."""
    mel = load_mel_module()
    
    # Create a Node.js project
    (tmp_path / "package.json").write_text('{"name":"test","scripts":{"test":"jest"}}')
    
    result = mel.detect_package_manager(tmp_path.as_posix())
    assert result == "npm"


def test_detect_package_manager_detects_yarn(tmp_path, monkeypatch):
    """Test that detect_package_manager detects yarn when yarn.lock exists."""
    mel = load_mel_module()
    
    # Create a yarn project
    (tmp_path / "package.json").write_text('{"name":"test"}')
    (tmp_path / "yarn.lock").write_text("# yarn lockfile v1")
    
    result = mel.detect_package_manager(tmp_path.as_posix())
    assert result == "yarn"


def test_detect_package_manager_detects_pnpm(tmp_path, monkeypatch):
    """Test that detect_package_manager detects pnpm when pnpm-lock.yaml exists."""
    mel = load_mel_module()
    
    # Create a pnpm project
    (tmp_path / "package.json").write_text('{"name":"test"}')
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'")
    
    result = mel.detect_package_manager(tmp_path.as_posix())
    assert result == "pnpm"


def test_run_script_by_name_handles_no_package_manager(tmp_path, monkeypatch):
    """Test that run_script_by_name handles projects without package managers gracefully."""
    mel = load_mel_module()
    
    # Set up a Python project without package.json
    mel_dir = tmp_path / ".mel"
    mel_dir.mkdir()
    (mel_dir / "config.json").write_text('{"main":"main","allow_package_scripts":true}')
    
    (tmp_path / "main.py").write_text("print('Hello, World!')")
    
    monkeypatch.setattr(mel, "repo_root", lambda: tmp_path.as_posix())
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")
    
    # Mock git commands
    def fake_run(cmd, check=True, cwd=None, env=None):
        return 0, ""
    
    monkeypatch.setattr(mel, "run", fake_run)
    
    cfg = mel.get_cfg(tmp_path.as_posix())
    
    # Try to run a script that doesn't exist in config or package.json
    rc = mel.run_script_by_name(cfg, "nonexistent", [])
    
    # Should return 1 (script not found) since no package manager is detected
    assert rc == 1
