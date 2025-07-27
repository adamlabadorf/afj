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

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('prompt', type=str)
def main(input_file, prompt):
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
    # Check for mock LLM environment variable
    if os.environ.get("AFJ_MOCK_LLM"):
        class MockResponse:
            def __init__(self, prompt):
                self._prompt = prompt
            def text(self):
                # Echo back the input prompt
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

    # Stage and commit in git
    subprocess.run(['git', '-C', str(script_dir), 'add', new_file.name], check=True)
    subprocess.run(['git', '-C', str(script_dir), 'commit', '-m', prompt], check=True)

    # Replace original file with new version
    shutil.copy(str(new_file), str(input_path))
    log(f"Updated {input_path} with new version.")

if __name__ == '__main__':
    main()
