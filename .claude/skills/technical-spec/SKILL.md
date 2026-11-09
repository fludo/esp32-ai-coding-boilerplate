---
name: technical-spec
description: Defines firmware architecture, configuration and secrets handling, and the PlatformIO build/test/quality commands for this ESP32 project. Use when configuring the build, designing firmware architecture, or running quality checks.
---

# Technical Design Rules

## Prerequisite Detection

Inspect `platformio.ini`, `scripts/check.sh`, CI definitions (`.github/workflows/`), `sdkconfig.defaults*` when present, and representative files under `src/`, `lib/`, `test/` before applying a command- or technology-specific rule. Treat a tool, environment, or framework as observed only when repository evidence names it. When a missing decision changes architecture, compatibility, hardware safety, or verification, stop and name the exact configuration or user decision required.

## Basic Technology Stack Policy

PlatformIO project, `espressif32` platform, Arduino-ESP32 core 3.x by default; ESP-IDF only when the esp32-platform skill's Framework Selection justifies it. Language: C++17 (`gnu++17` or newer as the toolchain provides) for project code; ESP-IDF C files keep C conventions. Select architecture by mapping requirements and constraints to explicit module responsibilities, task/loop ownership, data flow, and verification boundaries.

## Configuration and Secrets

### Build-time configuration
- Board- and feature-specific values are preprocessor flags set per environment in `platformio.ini` (`-D APP_<NAME>=<value>`) with documented defaults in `include/app_config.h`
- A default exists only when requirements define valid behavior for it; otherwise `#error` with the flag name and expected format
- Kconfig settings (ESP-IDF environments) live in `sdkconfig.defaults*`

### Runtime configuration
- Device-specific values that change after flashing (Wi-Fi credentials, broker URL, calibration) are stored in NVS (`Preferences`), read once through one configuration module, validated, and passed to consumers as typed values

### Secrets
- Credentials never appear in tracked files. Use gitignored `include/secrets.h` with a committed `include/secrets.example.h`, `${sysenv.VAR}` injection in `build_flags`, or runtime provisioning
- Logs and serial output never print secrets

## Architecture Design

### Architecture Design Principles
- **Responsibilities**: each module names the behavior it owns and what it delegates. Framework-free logic in `lib/`, hardware/framework adapters and wiring in `src/`
- **Execution ownership**: each piece of work has one execution context — `loop()`, a named FreeRTOS task, a timer callback, or an ISR — and the design names it. Cross-context data flow uses queues/notifications or a documented lock
- **State/data ownership**: each mutable or persisted value has one authoritative owner (RAM state, NVS key, file)
- **Resource budget**: the design states stack sizes for new tasks, static buffers, and the expected RAM/flash delta
- **Verification boundary**: each public contract has a host test (`native`), an on-target test, or a system check that can observe it

### Typical Firmware Layering

```
src/main.cpp           setup()/loop() or app_main: wiring, task start, top-level state
src/<adapter>.cpp      hardware/framework adapters implementing lib/ interfaces
lib/<module>/          framework-free logic + interfaces (host-tested)
include/app_config.h   build-flag defaults (pins, timings, feature switches)
test/native/           host Unity tests for lib/
test/embedded/         on-target Unity tests
```

## Unified Data Flow Principles

1. **Single data source**: store the same information in one place (one NVS key, one RAM owner)
2. **Structured data**: parse frames/payloads once at the input boundary into structs; pass structs, not raw strings
3. **Validation at input**: validate sensor values, received frames, and configuration at the boundary that receives them
4. **Bounded everything**: every buffer, queue, retry loop, and wait has an explicit bound

## Build and Testing

Commands use `pio` from PATH, or `~/.platformio/penv/bin/pio` when it is not on PATH.

### Build Commands
- `pio run -e <env>` — build one board environment (prints RAM/Flash usage)
- `pio run` — build `default_envs`
- `pio run -e <env> -t upload` / `pio device monitor -e <env>` — flash / monitor (hardware action; see esp32-platform skill)

### Testing Commands
- `pio test -e native` — host unit tests (`test/native/`), runs without hardware
- `pio test -e <env>` — on-target tests (`test/embedded/`), requires a connected board
- `pio test -e <env> --without-uploading --without-testing` — compile on-target tests without a board

### Quality Assurance Mechanism Awareness

Before executing quality checks, identify the mechanisms covering the change area:
- `scripts/check.sh` (authoritative quality command), CI workflows, `.clang-format`, `check_*` options in `platformio.ini`
- Which environments the change affects: a change in shared code (`lib/`, `include/`, `src/`, `[env]`) affects every board environment; a board-specific flag affects only that environment
- When a task file supplies Operation Verification Methods, run them as task-specific checks

### Quality Check Requirements

Quality checks are mandatory upon implementation completion. The authoritative command is **`scripts/check.sh`** (all board environments) — `scripts/check.sh --quick` or `-e <env>` narrows the build matrix during iteration, but the final gate for shared-code changes runs the full matrix.

**Phase 1: Format**
- `clang-format --dry-run --Werror` on changed C/C++ files (`scripts/check.sh --fix` applies it). When clang-format is not installed the gate fails: run `scripts/check.sh --no-format` and record the format check as unavailable

**Phase 2: Static analysis**
- `pio check -e <env> --skip-packages --fail-on-defect=medium --fail-on-defect=high` (cppcheck). Without `--fail-on-defect`, `pio check` reports PASSED even when defects are found — always pass it

**Phase 3: Build**
- `pio run -e <env>` for every affected environment with zero new warnings in project code (`build_src_flags = -Wall -Wextra`)

**Transition evidence**: every applicable static/build check exits successfully; missing tools are recorded with the exact reason.

**Phase 4: Tests**
- `pio test -e native` — all host suites pass
- On-target: `pio test -e <env>` when a board is attached and the change needs hardware evidence; otherwise the compiled embedded suites (last phase of `scripts/check.sh`) are the only evidence: record on-target execution as blocked with the prerequisite ("board for `<env>` attached")

**Transition evidence**: all host tests pass; on-target suites pass or are explicitly blocked with their prerequisite.

**Phase 5: Re-verification**
- Re-run `scripts/check.sh` (or the narrowed form used during iteration, followed by the full matrix) after test-related fixes

**Completion evidence**: format/static/build checks still pass after test fixes, and every required test has passed or is explicitly blocked.

### Auxiliary Commands
- `pio check -e <env> -v` — show every analyzed file and defect
- `pio run -e <env> -t size` / `pio run -e <env> -v` — size breakdown / full compiler command lines
- `pio pkg outdated` — show dependency updates before changing any version
- `pio run -t clean -e <env>` — clean one environment

### Troubleshooting
- **Library not found / wrong library picked**: inspect `lib_deps`, `lib_ldf_mode`, and the Library Dependency Graph in `pio run -v`. Fix the include or dependency, not by copying library code into `src/`
- **Build fails after a platform/core change**: compare against the pinned versions in `platformio.ini`; Arduino core 2.x → 3.x API changes are the usual cause
- **Dependency state corrupted**: `pio run -t clean -e <env>` first; `pio run -t fullclean` (re-downloads packages) only with approval
