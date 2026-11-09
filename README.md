# ESP32 AI Coding Boilerplate

A PlatformIO starter for ESP32 firmware developed with Claude Code. It combines the evidence-driven agent workflow of [ai-coding-project-boilerplate](https://github.com/fludo/ai-coding-project-boilerplate) with ESP32-specific skills, a multi-board build matrix, host-first tests and a quality gate.

- **Arduino first**: Arduino-ESP32 core 3.x on the official `espressif32 @ ~8.0.0` platform. ESP-IDF (as an Arduino component or on its own) is used only when a requirement needs it
- **Common boards ready to build**: ESP32 DevKit, ESP32-S3-DevKitC-1, ESP32-S2-Saola-1, ESP32-C3-DevKitM-1, LOLIN C3 Mini, ESP32-C6-DevKitC-1. Each env is one `[env:...]` section to keep or remove
- **Host-first testing**: framework-free logic in `lib/` is tested on your PC with `pio test -e native`. On-target Unity tests live in `test/embedded/`
- **One quality gate**: `scripts/check.sh` runs clang-format, cppcheck (`pio check --fail-on-defect`), native tests, the firmware build and the on-target test compile for every board. CI runs the same script
- **Hardware-aware agents**: skills for pins, boards, framework choice, embedded C++ rules, testing and crash triage. The rules require approval before data-loss actions (erase, partition/flash/PSRAM changes) and before flashing, and `.claude/settings.json` makes Claude Code prompt for upload, erase and `esptool` commands

## Quick Start

Requires PlatformIO Core (`pio`; the VS Code extension installs it at `~/.platformio/penv/bin/pio`), `clang-format`, Python 3.9+, git, and Claude Code.

```bash
git clone https://github.com/fludo/esp32-ai-coding-boilerplate.git
cd esp32-ai-coding-boilerplate
python3 scripts/new_project.py ~/PlatformIO/Projects/my-device
cd ~/PlatformIO/Projects/my-device
scripts/check.sh --quick
claude
```

In Claude Code:

```text
/project-inject
/implement Read a BME280 over I2C every 30 s and log the values
```

`/project-inject` records the device's purpose, boards, wiring source, test peers and constraints. `/implement` clarifies the request, inspects the code and boards, then implements directly or produces a Design Doc and Work Plan for approval. It writes host tests first and runs the quality gate.

See the [Quick Start Guide](docs/guides/quickstart.md) for the full walkthrough.

## Project Layout

```
platformio.ini            board environments + [env:native]; shared settings in [env]
src/main.cpp              setup()/loop(): wiring only
lib/<module>/             framework-free logic (host-testable)
include/app_config.h      per-board defaults overridable with -D APP_... build flags
include/secrets.example.h copy to include/secrets.h (gitignored)
test/native/              host Unity tests      → pio test -e native
test/embedded/            on-target Unity tests → pio test -e <board>
scripts/check.sh          quality gate
.claude/                  agents, commands, skills, settings.json (permission rules)
docs/guides/              usage guides
```

The example firmware blinks the status LED with a non-blocking, wraparound-safe pattern (`lib/blink_pattern`). It shows the split between `lib/` logic, `src/` wiring, per-board pins and the two test levels. Replace it with your application.

## Commands

| Goal | Command |
|---|---|
| Build / flash / monitor | `pio run -e <env>` · `pio run -e <env> -t upload` · `pio device monitor -e <env>` |
| Host tests | `pio test -e native` |
| On-target tests (board attached) | `pio test -e <env>` |
| Full quality gate | `scripts/check.sh` (`--quick`, `-e <env>`, `--fix`, `--no-format`) |

| What you want to do | Start with |
|---|---|
| Take a feature from request to verified implementation | `/implement` |
| Make a focused change | `/task` |
| Design before coding / plan / execute | `/design` → `/plan` → `/build` |
| Review completed work | `/review` |
| Investigate a crash, reset or bug without changing code | `/diagnose` (paste the serial log) |
| Add integration / on-target / system tests to existing code | `/add-integration-tests` |

See [Use Cases & Commands](docs/guides/use-cases.md) for the complete reference.

## ESP32 Skills

| Skill | Owns |
|---|---|
| `esp32-platform` | Framework choice (Arduino → Arduino+IDF → ESP-IDF → pioarduino), board environments, pins, flash/PSRAM/partition safety, `lib_deps`, secrets. Includes per-chip pin data for 9 chips |
| `esp32-cpp-rules` | `lib/` vs `src/` split, memory, non-blocking timing, FreeRTOS/ISR rules, error handling, logging |
| `esp32-testing` | Host → on-target → system test stages, Unity conventions, hardware test doubles |
| `integration-e2e-testing` | Choosing the smallest integration / on-target / system test set |
| `esp32-debugging` | Build, upload, panic, watchdog, Wi-Fi and BLE triage playbooks for PlatformIO |
| `technical-spec` | Firmware architecture rules and the build/test/quality commands |

The generic workflow skills (`coding-standards`, `documentation-criteria`, `implementation-approach`, `subagents-orchestration-guide`, …) come from the upstream boilerplate. Their TypeScript and frontend parts were removed.

## Workflow Modes

Normal Mode is the default. Lite Mode skips the independent design checks and the separate security review, and runs the quality gate once at the end instead of after each task:

```bash
python3 scripts/set_workflow_mode.py lite     # or: normal
```

## Keeping Projects Up to Date

Pull the boilerplate, then from the boilerplate checkout:

```bash
python3 scripts/update_ai_setup.py ~/PlatformIO/Projects/my-device --dry-run
python3 scripts/update_ai_setup.py ~/PlatformIO/Projects/my-device
```

This refreshes the managed agents, commands, skills, guides, `CLAUDE.md`, `.claude/settings.json` and `scripts/check.sh`, and removes managed files that the boilerplate deleted. It keeps your `project-context`, any project-only skills, the saved workflow mode, and all source and config.

The project's `.esp32-ai-boilerplate.json` records a hash of each managed file as installed. A managed file you edited is reported as `conflict` and left alone; pass `--force` to replace it. A project created before this record existed has every differing file reported as a conflict on its first update.

## Permission Rules

`.claude/settings.json` lets Claude Code run the quality gate, builds, static analysis and host tests without prompting, and always prompts for `pio run` with an upload or erase target, `esptool`, `espefuse` and `pio pkg exec`. Running on-target tests (`pio test -e <board>`, which flashes the board) is not pre-approved, so it prompts in the default permission mode. These rules match command text: they catch the usual invocations and are not a security boundary. Put personal overrides in `.claude/settings.local.json` (gitignored).

## Optional Add-on

[esp32-claude-workbench](https://github.com/agodianel/esp32-claude-workbench) provides an MCP server, CLI and Claude Code plugin with pin audits, crash decoding, partition and sdkconfig checks. It is aimed mainly at ESP-IDF projects. Its chip data and debugging playbooks are already vendored here, so install the plugin only if you want its tools:

```text
/plugin marketplace add agodianel/esp32-claude-workbench
/plugin install esp32-workbench@esp32-workbench
```

## Guides

- [Quick Start Guide](docs/guides/quickstart.md)
- [Use Cases & Commands](docs/guides/use-cases.md)
- [Skills Editing Guide](docs/guides/skills-editing-guide.md)
- [Skill Regression Prompts](docs/guides/skill-regression-prompts.md)

## License

[MIT](LICENSE) © 2026 Ludovic Favre. Includes material from MIT-licensed projects, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
