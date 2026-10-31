#!/usr/bin/env python3
"""Save the project's default workflow mode in CLAUDE.md.

    python3 scripts/set_workflow_mode.py lite|normal
"""

import sys
from pathlib import Path

LITE_DIRECTIVE = "Workflow Mode: Lite."


def get_workflow_mode(project_root: Path) -> str:
    rules = project_root / "CLAUDE.md"
    if not rules.exists():
        return "normal"
    lines = rules.read_text(encoding="utf-8").splitlines()
    return "lite" if any(line.rstrip() == LITE_DIRECTIVE for line in lines) else "normal"


def set_workflow_mode(mode: str, project_root: Path) -> None:
    if mode not in ("lite", "normal"):
        raise ValueError("Usage: python3 scripts/set_workflow_mode.py <lite|normal>")
    rules = project_root / "CLAUDE.md"
    content = rules.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in content else "\n"
    kept = [line for line in content.splitlines(keepends=True) if line.rstrip() != LITE_DIRECTIVE]
    updated = "".join(kept)
    if mode == "lite":
        updated = LITE_DIRECTIVE + newline + updated
    if updated != content:
        rules.write_text(updated, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/set_workflow_mode.py <lite|normal>", file=sys.stderr)
        return 1
    try:
        set_workflow_mode(sys.argv[1], Path.cwd())
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Workflow mode: {'Lite' if sys.argv[1] == 'lite' else 'Normal'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
