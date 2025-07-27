import os
import shutil
import tempfile
from pathlib import Path
import subprocess

import pytest

def test_afj_cli_basic(tmp_path):
    # Create a sample Python file
    input_file = tmp_path / "sample.py"
    input_file.write_text("print('original')\n")
    prompt = "Add a comment at the top."

    # Run the CLI using poetry
    env = os.environ.copy()
    env["AFJ_MOCK_LLM"] = "1"
    result = subprocess.run([
        "afj", str(input_file), prompt
    ], cwd=tmp_path, capture_output=True, text=True, env=env)

    # Check that the command ran successfully
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Check that the file was updated
    updated = input_file.read_text()
    assert "original" in updated
    assert "comment" in updated.lower() or "#" in updated

    # Check that .afj directory and git repo were created
    afj_dir = tmp_path / ".afj" / input_file.name
    assert afj_dir.is_dir()
    assert (afj_dir / ".git").is_dir()
    # Check that a .new file exists
    new_file = afj_dir / f"{input_file.name}.new"
    assert new_file.exists()
    # Check git log
    log_result = subprocess.run([
        "git", "-C", str(afj_dir), "log", "--oneline"
    ], capture_output=True, text=True)
    assert prompt in log_result.stdout
