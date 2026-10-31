# Quick Start

This guide takes a new ESP32 project from the boilerplate through initial setup and its first `/implement` run.

## Prerequisites

- PlatformIO Core (`pio`) — installed by the VS Code PlatformIO extension at `~/.platformio/penv/bin/pio`, or via `pipx install platformio`
- Python 3.9+ (already present with PlatformIO), git, Claude Code
- Optional: `clang-format` (format phase of `scripts/check.sh`), a board connected over USB for on-target tests
- WSL2: attach the board from Windows first (`usbipd list`, `usbipd attach --wsl --busid=<id>`)

## Create a project

From a clone of this boilerplate:

```bash
python3 scripts/new_project.py ~/PlatformIO/Projects/my-sensor
cd ~/PlatformIO/Projects/my-sensor
scripts/check.sh --quick      # native tests + static analysis + default board build
```

`new_project.py` copies the boilerplate without its git history, build output, or local plans, and initializes a new git repository. Alternatively, use the repository as a GitHub template.

Then pick your boards: keep the `[env:...]` sections you use in `platformio.ini`, set `default_envs` to the board on your desk, and add boards from `.claude/skills/esp32-platform/references/boards.md` if needed.

## Record project prerequisites

```bash
claude
```

```text
/project-inject
```

Use the hearing to record what changes agent decisions:

- the device's purpose and domain constraints (e.g. "the P1 port is read-only", "relay must default to off after reset");
- supported boards and the wiring source (schematic, pinout, or `app_config.h` flags);
- repository-specific acceptance standards;
- the current phase (prototype vs deployed devices with OTA — changes how cautious partition/NVS changes must be);
- access to datasheets, protocol specs, test peers (broker, AP, coordinator), and credentials provisioning.

The result is stored in `.claude/skills/project-context/SKILL.md` and loaded in later sessions. Re-run `/project-inject` when those prerequisites change.

## Implement a change

```text
/implement Read the BME280 over I2C every 30 s and log temperature, humidity and pressure
```

The workflow:

1. confirms the outcome, requirements, exclusions, and decision burden;
2. inspects the repository and boards before choosing an implementation (Arduino first; ESP-IDF only when a requirement forces it);
3. implements directly when one coherent small outcome has one evident path;
4. creates and obtains approval for the Design Doc and Work Plan for Medium/Large work, adding a PRD or ADR only when its decision is needed;
5. writes host tests first (`pio test -e native`), implements, runs `scripts/check.sh`, and commits approved changes;
6. runs on-target tests when a board is attached, and otherwise reports them as blocked rather than passed.

The workflow asks before hardware actions that can lose data (erasing flash, changing partitions, flash size or PSRAM settings) and before flashing a device unless you asked for it.

## Resume planned work

```text
/implement Continue the current implementation
/build docs/plans/20261031-feature-bme280.md
```

`/build` resolves the selected plan's task files, completes them one at a time, and preserves the Work Plan after removing consumed task files.

## Next references

- [Use Cases & Commands](./use-cases.md) — choose a command and inspect its boundary
- [Skills Editing Guide](./skills-editing-guide.md) — add project knowledge or reusable decision criteria
- [Skill Regression Prompts](./skill-regression-prompts.md) — check that the ESP32 rails still hold after editing skills
- [README](../../README.md) — overview and update instructions
