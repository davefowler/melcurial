import importlib.util
from importlib.machinery import SourceFileLoader
import pathlib
import types


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

    # Default when nothing present
    monkeypatch.chdir(tmp_path)
    assert mel.detect_package_manager(tmp_path.as_posix()) == "npm"

    # yarn
    (tmp_path / "yarn.lock").write_text("")
    assert mel.detect_package_manager(tmp_path.as_posix()) == "yarn"

    # pnpm has priority over yarn
    (tmp_path / "pnpm-lock.yaml").write_text("")
    assert mel.detect_package_manager(tmp_path.as_posix()) == "pnpm"


def test_run_tests_with_scripts_test_all_pass(tmp_path, monkeypatch):
    mel = load_mel_module()

    # Prepare repo root with .mel/config.json
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

    rc = mel.run_tests()
    assert rc == 0
    assert calls == ["cmd_test"]


def test_run_tests_with_scripts_test_fails(tmp_path, monkeypatch):
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

    rc = mel.run_tests()
    assert rc == 1


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


def test_import_global_template_when_no_repo_template(tmp_path, monkeypatch):
    mel = load_mel_module()
    monkeypatch.setattr(mel, "guess_main_name", lambda: "main")

    # Simulate a fake HOME with a template
    fake_home = tmp_path / "fakehome"
    (fake_home / ".mel").mkdir(parents=True)
    (fake_home / ".mel" / "config_template.json").write_text('{"scripts": {"test": "pytest -q"}}')

    original_expanduser = mel.os.path.expanduser
    monkeypatch.setattr(mel.os.path, "expanduser", lambda p: str(fake_home) if p == "~" else original_expanduser(p))

    cfg = mel.get_cfg(tmp_path.as_posix())
    assert cfg.get("scripts", {}).get("test") == "pytest -q"


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

    mel.cmd_open("repo")
    assert opened["url"] == "https://github.com/owner/repo"


