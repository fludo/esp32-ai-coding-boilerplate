#!/usr/bin/env python3
"""Create a new ESP32 project from this boilerplate.

    python3 scripts/new_project.py <target-dir> [--no-git]

Copies the boilerplate without git history, build output, local plans or
temporary files, records the boilerplate version in .esp32-ai-boilerplate.json,
and initializes a git repository with an initial commit.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ".esp32-ai-boilerplate.json"
EXCLUDE_DIRS = {".git", ".pio", "tmp", "__pycache__"}
EXCLUDE_FILES = {MANIFEST, "CHANGELOG.md"}


def boilerplate_version() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), "describe", "--tags", "--always", "--dirty"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def ignore(directory: str, names: list) -> set:
    rel = Path(directory).resolve().relative_to(ROOT)
    ignored = {n for n in names if n in EXCLUDE_DIRS or (rel == Path(".") and n in EXCLUDE_FILES)}
    # Work plans and task files are per-project; keep only plan templates.
    if rel == Path("docs/plans"):
        ignored |= {n for n in names if not n.startswith("template-")}
    # Only the extension recommendation; the rest of .vscode is machine-specific.
    if rel == Path(".vscode"):
        ignored |= {n for n in names if n != "extensions.json"}
    return ignored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--no-git", action="store_true", help="skip git init and the initial commit")
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        print(f"error: {target} exists and is not empty", file=sys.stderr)
        return 1
    if ROOT in target.parents:
        print("error: target must be outside the boilerplate", file=sys.stderr)
        return 1

    shutil.copytree(ROOT, target, ignore=ignore, dirs_exist_ok=True)
    manifest = {
        "boilerplate": str(ROOT),
        "version": boilerplate_version(),
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (target / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if not args.no_git:
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(target), "commit", "-q", "-m", "Initial commit from esp32-ai-coding-boilerplate"],
            check=False,
        )

    print(f"Created {target}")
    print("Next: cd into it, edit platformio.ini (boards, default_envs), run scripts/check.sh --quick, then `claude` and /project-inject")
    return 0


if __name__ == "__main__":
    sys.exit(main())
