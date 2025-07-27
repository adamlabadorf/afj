#!/usr/bin/env python3
import sys
import re
from pathlib import Path
import subprocess

def bump_version(version, part):
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("part must be one of: major, minor, patch")
    return f"{major}.{minor}.{patch}"

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)
    part = sys.argv[1]
    version_file = Path(__file__).parent / "VERSION"
    version = version_file.read_text().strip()
    new_version = bump_version(version, part)
    version_file.write_text(new_version + "\n")
    print(f"Version bumped to {new_version}")
    # Create a git tag
    subprocess.run(["git", "add", str(version_file)], check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)
    subprocess.run(["git", "tag", f"v{new_version}"], check=True)
    print(f"Git tag v{new_version} created.")

if __name__ == "__main__":
    main()
