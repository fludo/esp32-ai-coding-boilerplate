#!/usr/bin/env python3
"""Refresh the managed Claude Code setup of a project from the boilerplate.

    python3 <boilerplate>/scripts/update_ai_setup.py [project-dir] [--dry-run]

Run it from the boilerplate checkout you want to update *from* (pull it first).
Managed paths are replaced: .claude/agents, .claude/commands, .claude/skills,
CLAUDE.md, docs/guides, scripts/check.sh. Preserved: project-context skill,
any skill or command that exists only in the project, the saved workflow mode,
and everything else (source, platformio.ini, tests, docs/design, ...).

Commit the project first: local edits to managed files are overwritten.
"""

import argparse
import filecmp
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from set_workflow_mode import LITE_DIRECTIVE, get_workflow_mode, set_workflow_mode  # noqa: E402

SOURCE = Path(__file__).resolve().parent.parent
MANAGED_DIRS = [".claude/agents", ".claude/commands", ".claude/skills", "docs/guides"]
MANAGED_FILES = ["CLAUDE.md", "scripts/check.sh", "scripts/set_workflow_mode.py", "scripts/update_ai_setup.py"]
PRESERVED = {Path(".claude/skills/project-context")}
MANIFEST = ".esp32-ai-boilerplate.json"


def is_preserved(rel: Path) -> bool:
    return any(rel == p or p in rel.parents for p in PRESERVED)


def same_content(src: Path, dst: Path) -> bool:
    if src.name == "CLAUDE.md":
        # The saved workflow mode line is project state, not a managed difference.
        def strip(path):
            return [l for l in path.read_text(encoding="utf-8").splitlines() if l.rstrip() != LITE_DIRECTIVE]
        return strip(src) == strip(dst)
    return filecmp.cmp(src, dst, shallow=False)


def planned_changes(project: Path) -> list:
    changes = []
    for rel_dir in MANAGED_DIRS:
        for src in sorted((SOURCE / rel_dir).rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(SOURCE)
            if is_preserved(rel):
                continue
            dst = project / rel
            if not dst.exists():
                changes.append(("add", rel))
            elif not same_content(src, dst):
                changes.append(("update", rel))
    for name in MANAGED_FILES:
        src, dst = SOURCE / name, project / name
        if src.exists() and (not dst.exists() or not same_content(src, dst)):
            changes.append(("update" if dst.exists() else "add", Path(name)))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    if project == SOURCE:
        print("error: run this against a project, not the boilerplate itself", file=sys.stderr)
        return 1
    if not (project / "platformio.ini").exists():
        print(f"error: {project} has no platformio.ini", file=sys.stderr)
        return 1

    changes = planned_changes(project)
    if not changes:
        print("Already up to date.")
        return 0
    for kind, rel in changes:
        print(f"{kind:7} {rel}")
    if args.dry_run:
        print(f"\n{len(changes)} change(s) (dry run, nothing written)")
        return 0

    mode = get_workflow_mode(project)
    for _, rel in changes:
        dst = project / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / rel, dst)
    set_workflow_mode(mode, project)

    manifest_path = project / MANIFEST
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"\n{len(changes)} change(s) applied. Review with `git diff` in {project}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
