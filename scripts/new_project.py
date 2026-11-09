#!/usr/bin/env python3
"""Create a new ESP32 project from this boilerplate.

    python3 scripts/new_project.py <target-dir> [--no-git]

Copies the boilerplate's own files (tracked, or untracked and not gitignored),
so secrets, build output and local plans in this checkout never reach the new
project. The project gets its own README, no LICENSE (that choice is yours),
and a .esp32-ai-boilerplate.json recording the boilerplate version and the
managed files that scripts/update_ai_setup.py can refresh later.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_ai_setup import MANIFEST, SOURCE as ROOT, boilerplate_files, digest, is_managed, source_info  # noqa: E402

HOMEPAGE = "https://github.com/fludo/esp32-ai-coding-boilerplate"
# Files that describe or operate the boilerplate itself, not a project made from it.
BOILERPLATE_ONLY = {"README.md", "LICENSE", MANIFEST, "scripts/new_project.py", "scripts/update_ai_setup.py"}

README = """# {name}

ESP32 firmware built with PlatformIO and developed with Claude Code.

## Commands

| Goal | Command |
|---|---|
| Build / flash / monitor | `pio run -e <env>` · `pio run -e <env> -t upload` · `pio device monitor -e <env>` |
| Host tests | `pio test -e native` |
| On-target tests (board attached) | `pio test -e <env>` |
| Quality gate | `scripts/check.sh` (`--quick`, `-e <env>`, `--fix`) |

Secrets go in `include/secrets.h` (gitignored); copy `include/secrets.example.h`.

## Working with Claude Code

Run `/project-inject` once to record the device's purpose, boards and constraints, then start with
`/implement` or `/task`. See the [Quick Start Guide](docs/guides/quickstart.md) and
[Use Cases & Commands](docs/guides/use-cases.md).

Created from [esp32-ai-coding-boilerplate]({homepage}) ({version}). To refresh the agents, skills and
quality gate, pull a checkout of the boilerplate and run from it:

```bash
python3 scripts/update_ai_setup.py <this-project> --dry-run
```
"""


def write_notices(target: Path) -> None:
    """Keeps the boilerplate's MIT notice in the project without making it the project's license."""
    notices, license_file = target / "THIRD_PARTY_NOTICES.md", ROOT / "LICENSE"
    if not (notices.exists() and license_file.exists()):
        return
    head, sep, rest = notices.read_text(encoding="utf-8").partition("\n## ")
    section = (
        "\n\n## esp32-ai-coding-boilerplate\n\n"
        f"The project scaffold, `scripts/` and the ESP32 skills come from\n[esp32-ai-coding-boilerplate]({HOMEPAGE}), "
        "under the following license:\n\n"
        f"```\n{license_file.read_text(encoding='utf-8').strip()}\n```\n"
    )
    notices.write_text(head.rstrip() + section + sep + rest, encoding="utf-8")


def init_git(target: Path) -> None:
    def run(*args: str) -> None:
        subprocess.run(["git", "-C", str(target), *args], check=True, capture_output=True, text=True)

    run("init", "-q")
    run("add", "-A")
    try:
        run("commit", "-q", "-m", "Initial commit from esp32-ai-coding-boilerplate")
    except subprocess.CalledProcessError as error:
        print(
            "warning: git repository initialized and files staged, but the initial commit failed:\n"
            f"  {(error.stderr or error.stdout).strip()}\n"
            "  Fix the cause (often a missing user.name / user.email) and commit yourself.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--no-git", action="store_true", help="skip git init and the initial commit")
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        print(f"error: {target} exists and is not empty", file=sys.stderr)
        return 1
    if target == ROOT or ROOT in target.parents:
        print("error: target must be outside the boilerplate", file=sys.stderr)
        return 1

    files = [rel for rel in boilerplate_files() if rel.as_posix() not in BOILERPLATE_ONLY]
    for rel in files:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)

    info = source_info()
    (target / "README.md").write_text(
        README.format(name=target.name, homepage=HOMEPAGE, version=info["version"]), encoding="utf-8"
    )
    write_notices(target)
    manifest = {
        **info,
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "managed": {rel.as_posix(): digest(ROOT / rel) for rel in files if is_managed(rel)},
    }
    (target / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if not args.no_git:
        init_git(target)

    print(f"Created {target}")
    print("Next: cd into it, edit platformio.ini (boards, default_envs), run scripts/check.sh --quick, then `claude` and /project-inject")
    return 0


if __name__ == "__main__":
    sys.exit(main())
