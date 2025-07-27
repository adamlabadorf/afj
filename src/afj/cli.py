import os
import sys
import subprocess
from pathlib import Path
import shutil
import logging

import os
import sys
import subprocess
from pathlib import Path
import shutil
import logging
import click

# Try to import llm, but handle if not installed
try:
    import llm
except ImportError:
    llm = None

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

def log(msg):
    logging.info(msg)

def find_afj_dir(start_dir=None):
    """Locate or create the nearest .afj directory walking up from start_dir or cwd."""
    if start_dir is None:
        start_dir = Path.cwd()
    current = start_dir.resolve()
    while True:
        afj_dir = current / '.afj'
        log(f"Checking {afj_dir}")
        if afj_dir.is_dir():
            log("Found")
            return afj_dir
        if current == current.parent:
            break
        current = current.parent
    # Not found, create in cwd
    log("Didn't find .afj dir anywhere")
    afj_dir = Path.cwd() / '.afj'
    afj_dir.mkdir(parents=True, exist_ok=True)
    return afj_dir

def init_git_repo(script_dir):
    if not (script_dir / '.git').is_dir():
        log(f"Initializing git repo in {script_dir}")
        subprocess.run(['git', '-C', str(script_dir), 'init'], check=True)

@click.group()
def cli():
    """afj: AI-powered file modification and versioning CLI."""
    pass

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('prompt', type=str)
def mod_cmd(input_file, prompt):
    """Modify a file using an LLM and version changes."""
    input_path = Path(input_file).resolve()
    afj_dir = find_afj_dir(start_dir=input_path.parent)
    log(f"Using {afj_dir}")
    basename = input_path.name
    script_dir = afj_dir / basename
    script_dir.mkdir(parents=True, exist_ok=True)
    init_git_repo(script_dir)
    new_file = script_dir / f"{basename}.new"
    log(f"Input file: {input_file}")
    log(f"Sending prompt to LLM")

    # Read input file
    with open(input_path, 'r') as f:
        code_content = f.read()

    # Use llm to get new code (simulate if llm not installed)
    if os.environ.get("AFJ_MOCK_LLM"):
        class MockResponse:
            def __init__(self, prompt):
                self._prompt = prompt
            def text(self):
                return self._prompt
        class MockModel:
            def prompt(self, prompt):
                return MockResponse(prompt)
        model = MockModel()
        system = "You are a coding agent that writes and modifies code per the users request. You only output syntactically correct code in the language of the input"
        full_prompt = f"{system}\n\n{prompt}\n\n---\n{code_content}"
        response = model.prompt(full_prompt)
        new_code = response.text()
    elif llm is not None:
        system = "You are a coding agent that writes and modifies code per the users request. You only output syntactically correct code in the language of the input"
        full_prompt = f"{system}\n\n{prompt}\n\n---\n{code_content}"
        try:
            model = llm.get_model("gpt-4o-mini")
        except Exception:
            model = llm.get_default_model()
        response = model.prompt(full_prompt)
        new_code = response.text()
    else:
        new_code = f"# LLM output simulation\n{code_content}\n# Prompt: {prompt}"

    with open(new_file, 'w') as f:
        f.write(new_code)

    subprocess.run(['git', '-C', str(script_dir), 'add', new_file.name], check=True)
    subprocess.run(['git', '-C', str(script_dir), 'commit', '-m', prompt], check=True)
    shutil.copy(str(new_file), str(input_path))
    log(f"Updated {input_path} with new version.")

cli.add_command(mod_cmd, name='mod')
cli.add_command(mod_cmd, name='modify')

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
def rev_cmd(input_file):
    """Revert the script to the previous commit in its .afj repo."""
    input_path = Path(input_file).resolve()
    afj_dir = find_afj_dir(start_dir=input_path.parent)
    basename = input_path.name
    script_dir = afj_dir / basename
    git_dir = script_dir / '.git'
    if not git_dir.is_dir():
        log(f"No git repo found for {input_file}.")
        sys.exit(1)
    # Get previous commit hash
    result = subprocess.run([
        'git', '-C', str(script_dir), 'rev-parse', 'HEAD~1'
    ], capture_output=True, text=True)
    if result.returncode != 0:
        log("No previous commit to revert to.")
        sys.exit(1)
    prev_commit = result.stdout.strip()
    # Hard reset to previous commit
    subprocess.run([
        'git', '-C', str(script_dir), 'reset', '--hard', prev_commit
    ], check=True)
    # Copy reverted file back to input path
    new_file = script_dir / f"{basename}.new"
    if new_file.exists():
        shutil.copy(str(new_file), str(input_path))
        log(f"Reverted {input_file} to previous version.")
    else:
        log(f"No reverted file found at {new_file}.")
        sys.exit(1)

cli.add_command(rev_cmd, name='rev')
cli.add_command(rev_cmd, name='revert')

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
def his_cmd(input_file):
    """Show the change history for the input script."""
    input_path = Path(input_file).resolve()
    afj_dir = find_afj_dir(start_dir=input_path.parent)
    basename = input_path.name
    script_dir = afj_dir / basename
    git_dir = script_dir / '.git'
    if not git_dir.is_dir():
        log(f"No git repo found for {input_file}.")
        sys.exit(1)
    # Show git log for the file
    new_file = script_dir / f"{basename}.new"
    if not new_file.exists():
        log(f"No versioned file found at {new_file}.")
        sys.exit(1)
    result = subprocess.run([
        'git', '-C', str(script_dir), 'log', '--pretty=format:%h %s', '--', new_file.name
    ], capture_output=True, text=True)
    if result.returncode != 0:
        log("Failed to get git log.")
        sys.exit(1)
    print(result.stdout)

cli.add_command(his_cmd, name='his')
cli.add_command(his_cmd, name='history')

if __name__ == '__main__':
    cli()
