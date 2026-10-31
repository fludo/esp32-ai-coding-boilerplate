# Board Environments

Facts below were read from the official `espressif32` platform 8.0.0 board JSONs and the Arduino core 3.3.12 variants (`~/.platformio/packages/framework-arduinoespressif32/variants/`). When a value matters for a change, re-check the installed files; clones and board revisions differ.

## Environments in `platformio.ini`

| Env | Chip | Flash (board JSON) | Status LED | Serial / USB | Notes |
|---|---|---|---|---|---|
| `esp32dev` | ESP32 (2 cores) | 4 MB | Variant defines none → `-D APP_LED_PIN=2` (most DevKit clones) | USB-UART bridge (CP210x/CH340) | Generic WROOM-32 DevKitC and "ESP32 Dev Module" clones |
| `esp32-s3-devkitc-1` | ESP32-S3 (2 cores) | 8 MB | `RGB_BUILTIN` (WS2812 on GPIO48; GPIO38 on board v1.1) | `UART` port (bridge) by default; `USB` port is native | `ARDUINO_USB_MODE=1` preset. For N16R8 etc. set flash/PSRAM explicitly (see Board Safety) |
| `esp32-s2-saola-1` | ESP32-S2 (1 core) | 4 MB | `RGB_BUILTIN` (WS2812 on GPIO18) | USB-UART bridge | No Bluetooth |
| `esp32-c3-devkitm-1` | ESP32-C3 (1 core, RISC-V) | 4 MB | `RGB_BUILTIN` (WS2812 on GPIO8) | USB-UART bridge | Also the closest match for many "C3 Super Mini" boards (verify LED pin; often GPIO8, active-low plain LED) |
| `lolin_c3_mini` | ESP32-C3 (1 core) | 4 MB | `RGB_BUILTIN` (GPIO7) | Native USB only; `ARDUINO_USB_CDC_ON_BOOT=1` preset | Early output before USB enumerates is lost |
| `esp32-c6-devkitc-1` | ESP32-C6 (1 core + LP core) | 8 MB | `RGB_BUILTIN` (WS2812 on GPIO8) | Two ports: UART bridge and USB-Serial/JTAG | Wi-Fi 6, BLE 5, 802.15.4 (Zigbee/Thread via Arduino `Zigbee`/`OpenThread`) |
| `native` | host | — | — | — | Unit tests for `lib/` only |

In Arduino core 3.x, `digitalWrite(RGB_BUILTIN, HIGH/LOW)` drives the addressable LED (white/off), so the example firmware works unchanged on RGB boards. Use `rgbLedWrite(RGB_BUILTIN, r, g, b)` for colour.

## Other Boards Seen in Existing Projects

Add one of these as an environment when needed:

```ini
[env:esp32doit-devkit-v1]     ; ESP32, LED_BUILTIN = 2
board = esp32doit-devkit-v1

[env:lolin32]                 ; ESP32, LED_BUILTIN = 5
board = lolin32

[env:esp-wrover-kit]          ; ESP32 + PSRAM, RGB LED on GPIO0/2/4; variant defines no LED
board = esp-wrover-kit
build_flags =
    ${env.build_flags}
    -D APP_LED_PIN=2

[env:arduino_nano_esp32]      ; ESP32-S3, 16 MB, OPI PSRAM, DFU upload, Arduino pin numbering
board = arduino_nano_esp32    ; (BOARD_HAS_PIN_REMAP: D13 != GPIO13)

[env:adafruit_qtpy_esp32s3_n4r2] ; ESP32-S3 4 MB + 2 MB PSRAM, NeoPixel GPIO39 (power GPIO38)
board = adafruit_qtpy_esp32s3_n4r2

[env:wemos_d1_mini32]         ; ESP32 "D1 Mini" form factor
board = wemos_d1_mini32
```

## Not on the Official Platform

ESP32-H2, ESP32-P4 and ESP32-C5 boards are absent from `espressif32` 8.0.0. Options, in order:
1. pioarduino platform with a pinned release tag (Arduino core 3.x, same project layout)
2. `framework = espidf` on pioarduino
Record the choice and reason (esp32-platform skill, Framework Selection).

## Adding a Board

1. Find the board ID: `pio boards espressif32 | grep -i <name>`; read its JSON (`mcu`, `variant`, `extra_flags`, `upload.flash_size`, `arduino.memory_type`)
2. No exact match → pick the closest board with the **same chip, flash size and PSRAM type**, then override with `board_upload.flash_size`, `board_build.flash_mode`, `board_build.arduino.memory_type`, `board_build.partitions` — or drop the vendor's board JSON into `boards/` at the project root
3. Check `variants/<variant>/pins_arduino.h` for `LED_BUILTIN`/`RGB_BUILTIN`; if absent, set `-D APP_LED_PIN=<gpio>` from the schematic, or ask
4. Native-USB-only board → confirm `ARDUINO_USB_CDC_ON_BOOT=1` is in its JSON or add it to `build_flags`
5. Add `[env:<id>]` with only board-specific lines, add it to the CI matrix, build it (`pio run -e <id>`)
6. Add a row to the table above
