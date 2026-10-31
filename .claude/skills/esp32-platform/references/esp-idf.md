# Moving Down the Framework Ladder

Use only after the Framework Selection rules in `SKILL.md` justify it. Record the reason in a Design Doc or ADR.

## Arduino as an ESP-IDF Component (`framework = arduino, espidf`)

Keeps all Arduino code and APIs; ESP-IDF is compiled from source, so `sdkconfig.defaults` applies and managed components work. Verified with `espressif32` 8.0.0: the first build of the example takes ~3 minutes; incremental builds are fast.

```ini
[env:esp32dev-idf]
extends = env:esp32dev
framework = arduino, espidf
```

```
# sdkconfig.defaults (project root) — options Arduino needs, at least:
CONFIG_FREERTOS_HZ=1000
CONFIG_AUTOSTART_ARDUINO=y
```

On the first build PlatformIO generates `CMakeLists.txt` (root) and `src/CMakeLists.txt`, resolves managed components into `managed_components/` (with `dependencies.lock`), and writes `sdkconfig.<env>`. Commit the two `CMakeLists.txt`, `sdkconfig.defaults` and `dependencies.lock`; `managed_components/` and `sdkconfig.<env>` are generated and gitignored. Add your own managed components in `src/idf_component.yml`.

Differences to expect versus `framework = arduino`:
- The default partition table comes from ESP-IDF (1 MB app partition on a 4 MB ESP32 instead of Arduino's 1.25 MB); set `board_build.partitions` explicitly if the app needs more (see Board Safety)
- Kconfig defaults differ from Arduino's precompiled libraries (e.g. Bluetooth, log level): set what the requirement needs in `sdkconfig.defaults`
- Check the pinned Arduino core's documentation for any further required options before relying on a feature

## Pure ESP-IDF (`framework = espidf`)

Entry point is `extern "C" void app_main(void)`; no `setup()/loop()`, no Arduino APIs. `lib/` modules stay framework-free and keep their `native` tests. Logging uses `ESP_LOGx`, errors use `esp_err_t`, timing uses `esp_timer_get_time()` / `vTaskDelay(pdMS_TO_TICKS(ms))`.

## Kconfig and Components Hygiene

- Durable settings go in `sdkconfig.defaults` (or `sdkconfig.defaults.<target>`), never only in the generated `sdkconfig.<env>`; PlatformIO regenerates it when the target changes. Commit `sdkconfig.defaults`; treat `sdkconfig.<env>` as generated unless the project decided to commit it
- `pio run -t menuconfig -e <env>` explores options; copy the decided lines into `sdkconfig.defaults`
- `idf_component.yml` is the source of truth for managed components; never edit `managed_components/`. Verify component names/versions at https://components.espressif.com
- Prefer current drivers (`driver/i2c_master.h`, `driver/rmt_tx.h`, `esp_adc/adc_oneshot.h`) over legacy ones unless the pinned ESP-IDF predates them
- FreeRTOS on ESP-IDF: stack sizes are in **bytes**; delays in ticks (`pdMS_TO_TICKS`)

## Diagnostic Kconfig (debug builds only)

```
CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y        # keep the dump on screen instead of rebooting
CONFIG_FREERTOS_WATCHPOINT_END_OF_STACK=y
CONFIG_FREERTOS_CHECK_STACKOVERFLOW_CANARY=y
CONFIG_HEAP_POISONING_COMPREHENSIVE=y
CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH=y       # needs a coredump partition
```

Verify each option exists in the pinned ESP-IDF (menuconfig) and remove debug options before release.
