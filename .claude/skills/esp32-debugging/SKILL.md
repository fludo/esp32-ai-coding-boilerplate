---
name: esp32-debugging
description: Triages ESP32 firmware failures in a PlatformIO project - build/link errors, upload/flash failures, boot loops, Guru Meditation panics, backtraces, watchdog resets, stack overflows, brownouts, Wi-Fi/BLE drops - from logs to root cause. Use when a build, upload, or device run fails, or the user pastes a crash/serial log ("Guru Meditation", "Backtrace:", "abort()", "rst:0x", "wdt", "Brownout").
---

# ESP32 Failure Triage

Diagnose before changing code. A fix proposed from a crash goes through the normal workflow (`/diagnose` → `/task` or `/implement`).

## References

| Failure | Playbook |
|---|---|
| Compile / link / partition-size errors | [references/build-failure.md](references/build-failure.md) |
| Upload fails, port missing, boots into download mode | [references/flash-failures.md](references/flash-failures.md) |
| `Guru Meditation Error`, `abort()`, `LoadProhibited`, `Load access fault`, stack canary | [references/guru-meditation.md](references/guru-meditation.md) |
| `Task watchdog got triggered`, `Interrupt wdt timeout`, `rst:0x...(TG*WDT...)` | [references/watchdog-reset.md](references/watchdog-reset.md) |
| Wi-Fi disconnects/reason codes | [references/wifi-debug.md](references/wifi-debug.md) |
| BLE advertising/connection/GATT problems | [references/ble-debug.md](references/ble-debug.md) |

## Command Mapping (playbooks use `idf.py`)

| Playbook says | In this project |
|---|---|
| `idf.py build` | `pio run -e <env>` (`-v` for full command lines) |
| `idf.py -p PORT flash` | `pio run -e <env> -t upload [--upload-port PORT]` |
| `idf.py monitor` | `pio device monitor -e <env>` (`esp32_exception_decoder` filter decodes backtraces) |
| `idf.py set-target <chip>` | select / add the `[env:...]` for that board |
| `idf.py menuconfig` / `sdkconfig` edits | only for `espidf` environments: `pio run -e <env> -t menuconfig`, durable values in `sdkconfig.defaults` |
| `idf.py size` / `size-components` | `pio run -e <env> -t size` |
| `build/<app>.elf` | `.pio/build/<env>/firmware.elf` |
| `<prefix>addr2line` | `xtensa-<chip>-elf-addr2line` (ESP32/S2/S3) from `~/.platformio/packages/toolchain-xtensa-esp-elf*/bin/`, or `riscv32-esp-elf-addr2line` (C/H/P series) from `~/.platformio/packages/toolchain-riscv32-esp*/bin/`. Several versions can be installed side by side; use the one `pio run -e <env> -v` shows |
| `idf.py erase-flash` | `pio run -e <env> -t erase` — **wipes NVS; ask first** (esp32-platform Board Safety) |

## Steps

1. **Identify the environment and build**: which `[env:...]`, which board is attached, and whether the running firmware is the build being analyzed. A backtrace decoded with a different build's ELF gives wrong lines — rebuild-then-decode is only valid if the source is unchanged
2. **Capture the full log**: from the reset line (`rst:0x..`, `boot:0x..`) to the failure. `pio device monitor -e <env> | tee tmp/monitor.log`. The reset reason in the ROM banner (`POWERON`, `SW_CPU_RESET`, `TG1WDT_SYS_RESET`, `RTCWDT_RTC_RESET`, brownout) routes to the playbook
3. **Classify** with the playbook table above; for panics identify the architecture (Xtensa: `EXCCAUSE/EXCVADDR`; RISC-V: `MCAUSE/MTVAL/MEPC`)
4. **Decode**: the `esp32_exception_decoder` monitor filter (enabled in `platformio.ini`) prints `file:line` for Xtensa backtraces; for RISC-V or a saved log, run `addr2line -pfiaC -e .pio/build/<env>/firmware.elf <addresses>`
5. **Locate the cause in code** and state confidence with evidence (decoded frame, fault address pattern, reproducibility)
6. **Confirm** with the cheapest test: a host test reproducing the logic fault, or an on-target test / diagnostic build (e.g. `build_type = debug`, higher `CORE_DEBUG_LEVEL`, stack high-water-mark logging via `uxTaskGetStackHighWaterMark`)

## Common Root Causes in Arduino-ESP32 Code

- `loop()` or a task blocking without yielding → task watchdog; long `while (!WiFi...)` loops without timeout
- Default `loopTask` stack (8 KB) or a custom task stack too small for TLS/JSON/`printf` floats → stack canary
- `String`/heap churn in long-running code → fragmentation, `abort()` in `malloc` after hours
- ISR without `IRAM_ATTR` or calling `Serial`/logging → cache error / `Interrupt wdt timeout`
- Arduino core 2.x code on core 3.x (LEDC, timer, `analogWrite` resolution) → build errors or silent misbehavior
- Wrong board environment (flash size, PSRAM type) → boot loop right after upload
- Peripheral on a strapping/flash/USB pin → boot failure or lost console (esp32-platform `pin-limitations.md`)
- Brownout on Wi-Fi/BLE start → weak supply or cable; not a firmware bug, do not disable the detector

## Rules

- Never decode with the wrong toolchain or a different build's ELF; if decoding is impossible, say so — do not guess function names from addresses
- Never erase flash, change partitions, flash size, or PSRAM settings as a diagnostic step without approval
- Report: environment, firmware build, reset reason, decoded frames, root cause + confidence, the test that confirms it, and the proposed fix path
