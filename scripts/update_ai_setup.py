#!/usr/bin/env python3
"""Refresh the managed Claude Code setup of a project from the boilerplate.

    python3 <boilerplate>/scripts/update_ai_setup.py [project-dir] [--dry-run] [--force]

Run it from the boilerplate checkout you want to update *from* (pull it first).
Managed paths: .claude/agents, .claude/commands, .claude/skills, docs/guides,
.claude/settings.json, CLAUDE.md, scripts/check.sh, scripts/set_workflow_mode.py.

The project's .esp32-ai-boilerplate.json records a hash of every managed file
as it was installed. That record decides what happens to each file:

    add       new in the boilerplate
    update    changed in the boilerplate, untouched in the project
    remove    deleted from the boilerplate, untouched in the project
    conflict  edited in the project: kept as is, unless --force is given

Never touched: the project-context skill, files that exist only in the project
(your own skills, commands, agents), the saved workflow mode, and everything
outside the managed paths (source, platformio.ini, tests, docs/design, ...).
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from set_workflow_mode import LITE_DIRECTIVE, get_workflow_mode, set_workflow_mode  # noqa: E402

SOURCE = Path(__file__).resolve().parent.parent
MANAGED_DIRS = [".claude/agents", ".claude/commands", ".claude/skills", "docs/guides"]
MANAGED_FILES = [".claude/settings.json", "CLAUDE.md", "scripts/check.sh", "scripts/set_workflow_mode.py"]
PRESERVED = [Path(".claude/skills/project-context")]
MANIFEST = ".esp32-ai-boilerplate.json"
# Only used when the boilerplate is not a git checkout (e.g. a downloaded archive).
FALLBACK_EXCLUDE_DIRS = {".git", ".pio", ".vscode", "tmp", "__pycache__"}
FALLBACK_EXCLUDE_FILES = {"secrets.h", MANIFEST}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(SOURCE), *args], check=True, capture_output=True, text=True
    ).stdout


def boilerplate_files() -> list:
    """Files that belong to the boilerplate: tracked, or untracked and not gitignored."""
    try:
        rels = [Path(p) for p in git("ls-files", "-co", "--exclude-standard", "-z").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        rels = [
            p.relative_to(SOURCE)
            for p in SOURCE.rglob("*")
            if not FALLBACK_EXCLUDE_DIRS.intersection(p.relative_to(SOURCE).parts)
            and p.name not in FALLBACK_EXCLUDE_FILES
        ]
    return sorted(r for r in rels if (SOURCE / r).is_file())


def source_info() -> dict:
    """Where the boilerplate came from: remote URL and version, never a local path."""
    info = {}
    try:
        info["source"] = git("remote", "get-url", "origin").strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    try:
        info["version"] = git("describe", "--tags", "--always", "--dirty").strip()
    except (OSError, subprocess.CalledProcessError):
        info["version"] = "unknown"
    return info


def is_managed(rel: Path) -> bool:
    if any(rel == p or p in rel.parents for p in PRESERVED):
        return False
    return rel.as_posix() in MANAGED_FILES or any(Path(d) in rel.parents for d in MANAGED_DIRS)


def digest(path: Path) -> str:
    data = path.read_bytes()
    if path.name == "CLAUDE.md":
        # The saved workflow mode line is project state, not a managed difference.
        lines = data.decode("utf-8").splitlines(keepends=True)
        data = "".join(l for l in lines if l.rstrip() != LITE_DIRECTIVE).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def managed_digests() -> dict:
    return {rel.as_posix(): digest(SOURCE / rel) for rel in boilerplate_files() if is_managed(rel)}


def plan(project: Path, recorded: dict, force: bool):
    """Returns (changes, records): the actions to take and the manifest record after them."""
    source = managed_digests()
    changes, records = [], {}
    for rel, src_hash in source.items():
        dst = project / rel
        if not dst.exists():
            changes.append(("add", rel))
        elif digest(dst) == src_hash:
            pass
        elif force or digest(dst) == recorded.get(rel):
            changes.append(("update", rel))
        else:
            changes.append(("conflict", rel))
            if rel in recorded:
                records[rel] = recorded[rel]
            continue
        records[rel] = src_hash
    for rel, old_hash in recorded.items():
        dst = project / rel
        if rel in source or not dst.exists():
            continue
        if force or digest(dst) == old_hash:
            changes.append(("remove", rel))
        else:
            changes.append(("conflict", rel))
            records[rel] = old_hash
    return sorted(changes, key=lambda c: c[1]), records


def apply(project: Path, changes: list) -> None:
    mode = get_workflow_mode(project)
    for kind, rel in changes:
        dst = project / rel
        if kind in ("add", "update"):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / rel, dst)
        elif kind == "remove":
            dst.unlink()
            parent = dst.parent
            while parent != project and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    set_workflow_mode(mode, project)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true", help="list the changes without writing anything")
    parser.add_argument("--force", action="store_true", help="also overwrite or remove locally edited managed files")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    if project == SOURCE:
        print("error: run this against a project, not the boilerplate itself", file=sys.stderr)
        return 1
    if not (project / "platformio.ini").exists():
        print(f"error: {project} has no platformio.ini", file=sys.stderr)
        return 1

    manifest_path = project / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    recorded = manifest.get("managed")
    if recorded is None:
        print(
            "note: this project has no record of its managed files, so every file that differs\n"
            "      from the boilerplate counts as a local edit. Review them, then use --force.\n"
        )
        recorded = {}

    changes, records = plan(project, recorded, args.force)
    for kind, rel in changes:
        print(f"{kind:8} {rel}")
    conflicts = [rel for kind, rel in changes if kind == "conflict"]
    pending = len(changes) - len(conflicts)
    if changes:
        print()
    if conflicts:
        print(f"{len(conflicts)} locally edited file(s) kept. Re-run with --force to replace them.")
    if args.dry_run:
        print(f"{pending} change(s) (dry run, nothing written)")
        return 0

    updated = {k: v for k, v in manifest.items() if k != "boilerplate"}  # drop the legacy local path
    updated.update(source_info())
    updated["managed"] = records
    if pending == 0 and updated == manifest:
        print("Already up to date.")
        return 1 if conflicts else 0

    apply(project, changes)
    updated["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    print(f"{pending} change(s) applied. Review with `git diff` in {project}.")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
