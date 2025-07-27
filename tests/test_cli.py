import os
import shutil
import tempfile
from pathlib import Path
import subprocess

import pytest

def run_cli(args, tmp_path, env=None):
    if env is None:
        env = os.environ.copy()
    env["AFJ_MOCK_LLM"] = "1"
    return subprocess.run([
        "afj", *args
    ], cwd=tmp_path, capture_output=True, text=True, env=env)


def test_afj_mod_subcommand(tmp_path):
    input_file = tmp_path / "sample.py"
    input_file.write_text("print('original')\n")
    prompt = "Add a comment at the top."
    result = run_cli(["mod", str(input_file), prompt], tmp_path)
    assert result.returncode == 0, f"mod failed: {result.stderr}"
    updated = input_file.read_text()
    assert "original" in updated
    # The echo mock puts prompt in output
    assert prompt in updated
    afj_dir = tmp_path / ".afj" / input_file.name
    assert afj_dir.is_dir()
    assert (afj_dir / ".git").is_dir()
    new_file = afj_dir / f"{input_file.name}.new"
    assert new_file.exists()
    log_result = subprocess.run([
        "git", "-C", str(afj_dir), "log", "--oneline"
    ], capture_output=True, text=True)
    assert prompt in log_result.stdout


def test_afj_rev_subcommand(tmp_path):
    input_file = tmp_path / "sample.py"
    input_file.write_text("print('first')\n")
    prompt1 = "First change"
    prompt2 = "Second change"
    # First mod
    run_cli(["mod", str(input_file), prompt1], tmp_path)
    # Second mod
    run_cli(["mod", str(input_file), prompt2], tmp_path)
    # File should now have prompt2
    assert prompt2 in input_file.read_text()
    # Revert
    result = run_cli(["rev", str(input_file)], tmp_path)
    assert result.returncode == 0, f"rev failed: {result.stderr}"
    reverted = input_file.read_text()
    # After revert, file should have prompt1, not prompt2
    assert prompt1 in reverted
    assert prompt2 not in reverted


def test_afj_his_subcommand(tmp_path):
    input_file = tmp_path / "sample.py"
    input_file.write_text("print('first')\n")
    prompt1 = "First change"
    prompt2 = "Second change"
    run_cli(["mod", str(input_file), prompt1], tmp_path)
    run_cli(["mod", str(input_file), prompt2], tmp_path)
    result = run_cli(["his", str(input_file)], tmp_path)
    assert result.returncode == 0, f"his failed: {result.stderr}"
    # Should show two commits, most recent first
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(lines) >= 2
    assert prompt2 in lines[0] or prompt2 in result.stdout
    assert prompt1 in result.stdout
