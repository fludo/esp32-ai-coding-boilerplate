---
name: esp32-platform
description: Governs PlatformIO + ESP32 platform decisions - Arduino vs ESP-IDF framework selection, platform/core versions, board environments, pins, flash/PSRAM/partitions, lib_deps, secrets injection, and data-loss/brick safety. Use when adding a board or library, choosing pins, editing platformio.ini/sdkconfig/partitions, flashing, or deciding whether a feature needs ESP-IDF.
---

# ESP32 Platform and Board Rules

## References

- **[references/boards.md](references/boards.md)** — supported board environments, LED/USB/flash facts verified against the installed platform, how to add a board
- **[references/pin-limitations.md](references/pin-limitations.md)** — per-chip restricted pins (flash, strapping, input-only, USB, UART0, ADC2+Wi-Fi) and a pin checklist
- **[references/chips/](references/chips/)** — per-chip JSON pin facts with Espressif source links (esp32, s2, s3, c2, c3, c5, c6, h2, p4)
- **[references/esp-idf.md](references/esp-idf.md)** — switching an environment to Arduino-as-component or pure ESP-IDF, `sdkconfig.defaults`, components

## Read Before Writing

- `platformio.ini`: identify the **active environment** (`default_envs` or `-e <env>`) and what it inherits from `[env]`. Every change states which environments it affects
- `boards/*.json` at the project root, if present (overrides platform board definitions silently)
- `sdkconfig.defaults*` and `partitions*.csv` referenced by `board_build.partitions`, when present
- The installed platform: `pio pkg list -g -p espressif32` (or `~/.platformio/platforms/espressif32*/platform.json`) and board JSONs under `~/.platformio/platforms/espressif32/boards/`

## Framework Selection (Arduino first)

Default to **Arduino-ESP32 core 3.x** (`framework = arduino`) on the official platform (`platform = espressif32 @ ~8.0.0`, Arduino core 3.3.x on ESP-IDF 5.x). Move down the ladder only when a named requirement forces it, and record the reason in the Design Doc or ADR:

1. **`framework = arduino`** — default. Arduino APIs plus direct ESP-IDF calls (`esp_*.h`, FreeRTOS, `driver/*.h`) are available from Arduino code, so "needs one IDF API" is *not* a reason to switch
2. **`framework = arduino, espidf`** (Arduino as an ESP-IDF component) — when the requirement needs a Kconfig option the precompiled Arduino libs do not set (custom `sdkconfig.defaults`, e.g. Bluetooth controller mode, PSRAM tuning, partition/coredump settings, mbedTLS options), or an ESP-IDF managed component via `idf_component.yml`
3. **`framework = espidf`** — when Arduino has no support for the chip or stack (check `boards.md`), when the project needs full control of startup/memory (very tight RAM, ULP/LP core focus), or when the requirement names an ESP-IDF-only example/stack whose Arduino port is missing or unfit
4. **pioarduino platform** (`platform = https://github.com/pioarduino/platform-espressif32/releases/download/<tag>/platform-espressif32.zip`) — only when the official platform lacks a chip/board (ESP32-H2, ESP32-P4, ESP32-C5 at the time of writing) or a newer Arduino core is required. Pin the exact release tag

Before choosing, check the requirement against the current Arduino core: Wi-Fi, BLE (Bluedroid or NimBLE backend), Zigbee (`Zigbee.h`, C6/H2), Matter, Thread/OpenThread, ESP-NOW, USB (S2/S3), LEDC, RMT, I2S are available in Arduino core 3.x. Verify a specific API by grepping `~/.platformio/packages/framework-arduinoespressif32/` (cores/, libraries/) rather than from memory.

## Don't Fabricate

- **GPIO numbers**: never invent one. The chip's GPIOs, the module's free pins, and the pins a board breaks out differ. Take pins from the user, a linked schematic/pinout, or the board variant (`variants/<variant>/pins_arduino.h`). Check every chosen pin against `pin-limitations.md` for each targeted chip
- **Board IDs**: verify with `pio boards espressif32 | grep -i <pattern>` (or the board JSON) before writing `board =`. A wrong board means wrong flash size, PSRAM mode, USB mode, and variant pins
- **Peripheral/radio availability** differs per chip (BT Classic only on ESP32; 802.15.4 only on C6/H2; USB-OTG on S2/S3; no Wi-Fi on H2/P4; ADC2 limits). Check the chip JSON before generalizing
- **APIs**: Arduino core 2.x → 3.x renamed APIs (LEDC `ledcAttach`/`ledcWrite` by pin, timer API, `rgbLedWrite`, `ETH`, BLE). Confirm a function exists in the installed core before using it; old forum code is often 2.x
- **Libraries**: verify name, owner and version in the registry (`pio pkg search "<name>"`, https://registry.platformio.org) and check it declares `espressif32` + the framework in use. Prefer registry packages over Git URLs

## Board Safety (data loss / brick risks)

Ask before, and name what is destroyed, when an action does any of the following:

- **Erasing flash** (`pio run -t erase`, `esptool erase_flash`) wipes NVS (Wi-Fi credentials, pairing/commissioning data, calibration), the filesystem partition and OTA state. Never use it as a debugging step
- **Changing flash size, flash mode or PSRAM type** (`board_upload.flash_size`, `board_build.flash_mode`, `board_build.arduino.memory_type`, `board_build.psram_type`, `BOARD_HAS_PSRAM`) without confirming the module part number (e.g. N8R8, N16R8, N4R2) can boot-loop the board. Octal-PSRAM modules also reserve GPIO33-37 on S3
- **Changing the partition table** (`board_build.partitions`) moves or shrinks partitions and wipes their data; OTA-deployed devices cannot be repartitioned over the air. Grow free space, do not reorder
- **Writing eFuses, enabling flash encryption or secure boot** is irreversible
- **Disabling the brownout detector or watchdogs** to hide resets is not a fix
- **Reconfiguring USB D-/D+ pins** as GPIO on S2/S3/C3/C6 removes the USB console; recovery requires holding BOOT during reset
- **`pio run -t fullclean`** forces large re-downloads; use `-t clean` for routine cleans. **`pio pkg update`** bumps everything without a diff; run `pio pkg outdated` first and update one dependency at a time

## platformio.ini Conventions

- Shared settings live in `[env]`; each board env adds only its own `board` and board-specific `build_flags` (`${env.build_flags}` to extend). Use `extends = env:<name>` for variants of one board instead of copying blocks
- One environment per physical board/module variant plus `[env:native]`; do not create envs for minor flag variations
- Pin the platform (`espressif32 @ ~8.0.0`) and every `lib_deps` entry (`owner/name @ ^x.y.z`) for reproducible builds
- Board-specific values (pins, feature switches) are `-D APP_<NAME>=<value>` flags with defaults in `include/app_config.h`
- `default_envs` reflects the board currently wired up. When a command targets another board, pass `-e <env>` and say so
- Never edit or commit `.pio/`

## Secrets

- Never hard-code Wi-Fi credentials, MQTT passwords, API keys, or device certificates in source or `platformio.ini`
- Use one of: a gitignored `include/secrets.h` (commit `include/secrets.example.h` with placeholder values), build-time injection from the environment (`build_flags = -D WIFI_SSID=\"${sysenv.WIFI_SSID}\"`), or runtime provisioning into NVS (WiFiManager/Improv/BLE provisioning)
- When the user hands credentials in chat, put them in the gitignored location, never in a tracked file
- Never log secrets, even at debug level

## Upload, Monitor and Ports

- `pio run -e <env> -t upload`, `pio device monitor -e <env>` (uses `monitor_speed`/`monitor_filters`), `pio device list`
- Native-USB boards (C3/C6/S3 USB port, `ARDUINO_USB_CDC_ON_BOOT=1`) re-enumerate on reset: the port can change, and output before USB is up is lost. If upload fails, hold BOOT, tap RESET, release BOOT
- WSL2: USB devices must be attached from Windows (`usbipd list`, `usbipd attach --wsl --busid=<id>`) before `/dev/ttyUSB*`/`/dev/ttyACM*` exists
- Flashing a device is an external action on hardware: do it when the user asked for it or the invoked workflow requires on-target verification and a board is attached

## Memory Budget

`pio run` prints `RAM:` and `Flash:` usage. Report the delta for changes that add libraries, buffers, tasks, or features. Above ~85 % flash of the app partition, flag OTA headroom; consider a larger app partition only with the partition-change rule above.
