import os
import subprocess
import tempfile
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MEL = REPO_ROOT / "mel"


def run(cmd, cwd=None, env=None, timeout=20):
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env_vars,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    return proc.returncode, out


def test_init_creates_repo_local_mel_and_plugins(tmp_path):
    cwd = tmp_path
    # init a git repo
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    rc, out = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    assert (cwd / ".mel").is_dir()
    assert (cwd / ".mel" / "plugins" / "core").is_dir()
    assert (cwd / ".gitignore").exists()
    assert "Available commands:" in out


def test_template_apply_merges_template_after_init(tmp_path):
    cwd = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    # First run creates .mel
    rc, _ = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    # Add template and apply
    (cwd / ".mel").mkdir(exist_ok=True)
    (cwd / ".mel" / "config_template.json").write_text('{"scripts":{"hello":"echo hi"}}')
    rc, _ = run([str(MEL), "template:apply"], cwd=cwd)
    assert rc == 0
    # Now help should include hello
    rc, out = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    assert "hello" in out
    # Execute hello
    rc, out = run([str(MEL), "hello"], cwd=cwd)
    assert rc == 0
    assert "hi" in out


def test_docs_plugin_serves_docs_directory(tmp_path):
    cwd = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    # Initialize and install docs plugin
    rc, _ = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    rc, _ = run([str(MEL), "plugin", "install", "mel-docs"], cwd=cwd)
    assert rc == 0
    (cwd / "docs").mkdir()
    (cwd / "docs" / "index.html").write_text("ok")
    # Launch server briefly
    proc = subprocess.Popen([str(MEL), "docs", "--port", "8765", "--host", "127.0.0.1"], cwd=cwd)
    time.sleep(1.0)
    proc.terminate()
    proc.wait(timeout=10)


def test_hg_plugin_writes_hgignore(tmp_path):
    cwd = tmp_path
    # No hg repo required for ignore file creation
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    rc, _ = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    rc, _ = run([str(MEL), "plugin", "install", "hg"], cwd=cwd)
    assert rc == 0
    assert (cwd / ".mel" / "plugins" / "hg").is_dir()
    # Run ignore script explicitly to ensure file creation
    ignore_script = cwd / ".mel" / "plugins" / "hg" / "bin" / "ignoremel.sh"
    rc, _ = run(["bash", str(ignore_script)], cwd=cwd)
    assert rc == 0
    assert (cwd / ".hgignore").exists()


def test_mode_switch_and_help_filtering(tmp_path):
    cwd = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    rc, _ = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    # Install docs plugin (advanced command) to test filtering
    rc, _ = run([str(MEL), "plugin", "install", "mel-docs"], cwd=cwd)
    assert rc == 0
    # Default is basic: docs should not show
    rc, out = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    assert "docs" not in out
    # Switch to advanced
    rc, _ = run([str(MEL), "mode", "advanced"], cwd=cwd)
    assert rc == 0
    rc, out = run([str(MEL), "help"], cwd=cwd)
    assert rc == 0
    assert "docs" in out


