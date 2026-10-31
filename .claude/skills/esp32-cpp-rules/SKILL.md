---
name: esp32-cpp-rules
description: Applies embedded C++ rules for ESP32 firmware - memory, timing, concurrency, ISR safety, error handling, and hardware isolation for Arduino-ESP32 and ESP-IDF code. Use when implementing or reviewing firmware code.
---

# ESP32 Firmware C++ Rules

## Prerequisite Detection

Inspect `platformio.ini` (platform version, `framework`, `board`, `build_flags`, `lib_deps`), `sdkconfig.defaults` when ESP-IDF is involved, `.clang-format`, and representative files under `src/`, `lib/`, `include/` before applying project conventions. Determine for the changed code: which framework owns it (Arduino API, ESP-IDF API, or framework-free), which chips the touched environments target, and whether it must also compile for the `native` environment. Treat a rule as project-specific only when configuration or an established pattern supports it. When competing conventions change a public interface, a pin assignment, timing behavior, or memory budget, stop and name the source or user decision required.

## Code Layout and Hardware Isolation

| Location | Owns | May include |
|---|---|---|
| `lib/<module>/` | Hardware-independent logic: parsing, state machines, protocols, calculations | C++ standard library, other framework-free `lib/` modules. **No** `Arduino.h`, `esp_*.h`, FreeRTOS headers |
| `src/` | Wiring: setup/loop or `app_main`, peripheral drivers, adapters that implement `lib/` interfaces | Framework headers |
| `include/` | Project-wide configuration headers (pin map defaults, feature switches) | Preprocessor defaults only |
| `test/native/` | Host tests for `lib/` modules | Unity + the module under test |
| `test/embedded/` | On-target tests that need real hardware or the framework | Unity + framework |

- A module goes in `lib/` when its behavior can be decided without hardware; inject time, I/O, and randomness through parameters or a small interface so the `native` environment can test it
- Pass time as a value (`uint32_t now_ms`) instead of calling `millis()` inside `lib/` code
- An adapter in `src/` translates between the framework and a `lib/` interface; keep business decisions out of adapters

## Board and Pin Configuration

- Never hard-code a GPIO number in logic. Read pins from a build flag with a default in `include/` (`#ifndef APP_LED_PIN`), or from the board variant macro (`LED_BUILTIN`, `RGB_BUILTIN`) when the variant defines it
- Board differences live in `platformio.ini` environments (`build_flags = -D APP_...`), not in `#if` chains on board names inside logic
- Use `CONFIG_IDF_TARGET_ESP32*` / `SOC_*` capability macros (e.g. `SOC_WIFI_SUPPORTED`, `SOC_BT_SUPPORTED`, `SOC_IEEE802154_SUPPORTED`, `SOC_USB_OTG_SUPPORTED`) when code must adapt to a chip capability; prefer a capability macro over a chip-name macro
- Before using a GPIO, check the esp32-platform skill's restricted-pin notes (strapping, flash/PSRAM, input-only, USB pins) for every chip the touched environments target

## Memory

- Size fixed buffers from a named constant and bound every write (`snprintf`, `strncpy` + explicit terminator, length-checked `memcpy`). Treat `sprintf`, `strcpy`, `strcat`, `gets` as defects
- Avoid heap allocation in `loop()`, callbacks, and periodic tasks. Allocate once at setup, or use fixed-capacity containers. Repeated `String` concatenation and `std::string` growth in hot paths fragment the heap; build into a reserved buffer instead
- Check every allocation result (`malloc`, `heap_caps_malloc`, `new (std::nothrow)`) and route the failure to the owning outcome
- Large buffers (> ~1 KB) do not go on a task stack unless the stack size was sized for them; prefer static storage or a one-time heap allocation. Use `heap_caps_malloc(..., MALLOC_CAP_SPIRAM)` only when the target environment enables PSRAM
- Constant tables use `const`/`constexpr` so they stay in flash
- When a change adds a buffer, task, or library, report the RAM/flash delta from `pio run` (`RAM: ... Flash: ...` lines) for the default environment

## Timing and the Main Loop

- `loop()` and task bodies never block on `delay()` longer than the responsiveness requirement allows; use non-blocking state machines driven by `millis()`/`esp_timer_get_time()` or FreeRTOS waits with a timeout
- Compute elapsed time as `static_cast<uint32_t>(now - start) >= interval` so `millis()` wraparound (~49.7 days) stays correct; never compare absolute deadlines with `<`
- Every blocking wait (`xQueueReceive`, `xSemaphoreTake`, `WiFi` connect loops, `Serial.readBytes`) has a finite timeout unless the requirement states the task must wait forever
- Long-running loops call `delay(0)`/`vTaskDelay`/`yield()` or wait on an RTOS primitive so the idle task runs and the task watchdog is fed

## Concurrency and ISRs

- ISR handlers are marked `IRAM_ATTR`, do minimal work, and hand off through `xQueueSendFromISR`/`xTaskNotifyFromISR`/`portYIELD_FROM_ISR`. No `Serial`, `printf`, `ESP_LOG*`, heap allocation, `delay`, or non-ISR FreeRTOS calls inside an ISR
- Data shared with an ISR is `volatile` and accessed under `portENTER_CRITICAL`/`portENTER_CRITICAL_ISR` with a `portMUX_TYPE` when wider than one aligned word or updated read-modify-write. Prefer `std::atomic` for single values
- Data shared between tasks has one owner; other tasks communicate with it through a queue, or a mutex guards it. Name the owner in a comment at the declaration
- Task creation states stack size, priority, and core explicitly (`xTaskCreatePinnedToCore`); dual-core assumptions are guarded (`#if !CONFIG_FREERTOS_UNICORE`) because ESP32-S2/C3/C6/H2 are single-core
- Wi-Fi/BLE/Zigbee callbacks run in stack-owned tasks; keep them short and hand work to an application task

## Error Handling

**Error Outcome Rule**: Every failure has one owning outcome: return an error code to a caller that can act, recover according to a named requirement (retry with bounded backoff, fallback mode), or stop with a diagnostic. Log once, at the boundary that owns the outcome.

- ESP-IDF calls return `esp_err_t`: check each one. Use `ESP_ERROR_CHECK` only where failure means the device cannot continue (init of a required peripheral); elsewhere propagate with `ESP_RETURN_ON_ERROR` or explicit handling
- Arduino calls that report failure (`begin()` returning `false`, `WiFi.status()`, `Wire.endTransmission()` non-zero) are checked; do not ignore boolean results
- Framework-free `lib/` code returns a result (`bool` + out-parameter, an enum status, or a small `struct { Status status; T value; }`) instead of throwing. Exceptions are off by default in ESP-IDF builds; do not introduce `throw` unless the project enables `CONFIG_COMPILER_CXX_EXCEPTIONS`
- Reboot (`ESP.restart()` / `esp_restart()`) is a recovery decision owned by one place and recorded in the design; a silent restart loop hides faults
- Do not swallow errors with an empty branch; a deliberate ignore states the reason in a comment

## Logging and Sensitive Data

- Use `ESP_LOGx(TAG, ...)` (works under both Arduino and ESP-IDF) or `log_x(...)` in Arduino code, with `static const char *TAG = "module"` per file; avoid raw `Serial.print` debug output in committed code outside `main.cpp` bring-up
- Control verbosity with `CORE_DEBUG_LEVEL` / `CONFIG_LOG_DEFAULT_LEVEL` build flags, not by editing call sites
- Never log Wi-Fi passwords, API tokens, MQTT credentials, or device keys. Credentials come from a gitignored header (`include/secrets.h`) or NVS provisioning, never from committed source

## Power, Persistence, and Wear

- Writes to NVS/`Preferences`/LittleFS are event-driven or rate-limited; no flash writes on every loop iteration or sensor sample
- `Preferences.begin()` is paired with `end()`; NVS keys are ≤ 15 characters
- Peripherals that the requirement allows to sleep are released or powered down at the owning lifecycle boundary; deep-sleep entry documents its wake sources

## Coding Conventions

- Follow `.clang-format`; types `PascalCase`, functions and variables `camelCase` (Arduino style) unless the touched code is ESP-IDF C, which keeps `snake_case`. Match the file you are editing
- Constants: `constexpr` with `k` prefix (`kBlinkIntervalMs`) in C++, `UPPER_SNAKE` macros only for preprocessor configuration
- Fixed-width integer types (`uint8_t`, `uint32_t`) for hardware values, protocol fields, and time
- Classes are allowed and idiomatic (drivers, state machines); keep constructors free of hardware access. Initialize hardware in an explicit `begin()` called from `setup()`, because global constructors run before the framework is ready
- Header files use `#pragma once`; a `lib/` module exposes one public header named after the module
- Remove debug prints, commented-out code, and unused includes within the change. Comments explain why (timing constraints, datasheet references, errata), not what
- Compiler warnings in project code (`build_src_flags = -Wall -Wextra`) are treated as failures for the changed files
