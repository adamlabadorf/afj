# afj

A CLI tool for AI-powered file editing and code augmentation with full version control.

---

## Overview

**afj** is a command-line tool that leverages large language models (LLMs) to automate code and text modifications based on natural language prompts. It provides:

- Automatic code or text editing via LLMs
- Version control for every change (using Git)
- Easy integration into developer workflows

---

## Installation

### Prerequisites
- Python 3.13+
- [Poetry](https://python-poetry.org/) (recommended for development)
- `git` installed and available in your PATH

### Install from Source
```bash
# Clone the repository
 git clone <your-repo-url>
 cd afj

# Install dependencies
poetry install

# Install the CLI command (in your environment)
poetry run pip install --editable .
```

## Installation

### 1. Install afj

```bash
pip install .
```

### 2. Configure the llm package

The `afj` tool uses the [`llm`](https://github.com/simonw/llm) Python package to communicate with language models. You must configure a default LLM model before using `afj`.

#### Example: Configure OpenAI GPT-4o as default
```bash
# Set your OpenAI API key (replace with your key)
llm keys set openai sk-...

# Set OpenAI GPT-4o as the default model
llm models default o4-mini
```

You can use any provider supported by the `llm` package. See the [llm documentation](https://llm.datasette.io/en/stable/) for details on configuring other providers/models.

> **Note:** `afj` will use whatever the default model is set in `llm`. You can change the default model at any time using `llm` commands.

---

## Basic Usage

```bash
afj <input_file> <prompt>
```

- `<input_file>`: Path to the file you want to modify (e.g., `main.py`)
- `<prompt>`: Natural language instruction for the LLM (e.g., "Add a docstring to all functions.")

### Example
```bash
afj my_script.py "Add a comment at the top."
```

---

## Subcommands

afj now supports multiple subcommands for advanced file versioning workflows:

### `mod` / `modify`
Modify a file using an LLM and version the changes (default functionality).

```bash
afj mod <input_file> <prompt>
# or
afj modify <input_file> <prompt>
```

- Modifies the file using your prompt and the LLM.
- Saves the new version in `.afj/<filename>/`, commits to git, and replaces the original file.

### `rev` / `revert`
Revert the input script to the previous commit in its `.afj` repo and hard reset the repo.

```bash
afj rev <input_file>
# or
afj revert <input_file>
```

- Rolls back the file to the previous version as tracked by afj's internal git repo.
- The file and the repo are both reset to that state.

### `his` / `history`
Show a simply formatted git log of the change history for the input script.

```bash
afj his <input_file>
# or
afj history <input_file>
```

- Outputs a concise commit history for the file as tracked by afj.

---

## How the `afj` Command Works

1. **Input**: You provide a file and a prompt.
2. **Prompt Construction**: afj constructs a system prompt for the LLM, including the current file content and your instruction.
3. **LLM Request**: The tool sends the prompt to the LLM (using the `llm` Python package, with GPT-4o-mini or fallback model).
4. **File Update**: The LLM's response is written to a `.new` file in a dedicated `.afj/<filename>/` directory.
5. **Version Control**: All changes are committed to a local git repository inside `.afj/<filename>/`.
6. **File Replacement**: The original file is replaced with the new version.
7. **Traceability**: You can view the git log in `.afj/<filename>/` to see all changes and prompts.

### Directory Structure Example
```
my_script.py
.afj/
  my_script.py/
    .git/
    my_script.py.new
```

### Notes
- If the `llm` package is not installed, afj will simulate output for testing.
- For testing, you can set the environment variable `AFJ_MOCK_LLM=1` to make the tool echo the prompt instead of calling a real LLM.

---

## Development & Testing

- Run tests with:
  ```bash
  poetry run pytest
  ```
- The CLI can be run directly via `afj` if installed, or with `poetry run afj ...` in development.
- Tests mock LLM calls for speed and reliability.

---

## License
MIT

---

## Author
Adam Labadorf (<labadorf@bu.edu>)
