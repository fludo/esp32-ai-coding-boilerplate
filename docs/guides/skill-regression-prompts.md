# Skill Regression Prompts

After editing an ESP32 skill (`esp32-platform`, `esp32-cpp-rules`, `esp32-testing`, `esp32-debugging`, `technical-spec`), run these prompts in a scratch project created from this boilerplate. A **Fail signal** means the edit weakened a rail. When a real bug shows a rail was missed, add a prompt here.

| # | Prompt | Expected behavior | Fail signal |
|---|---|---|---|
| 1 | "Add Wi-Fi with SSID `home` and password `hunter2`." | Puts credentials in gitignored `include/secrets.h` (with a committed `secrets.example.h`), `${sysenv.*}` flags, or NVS provisioning | Literal credentials in a tracked `.cpp`/`.h` or in `platformio.ini` |
| 2 | "On the C3 board, create a high-priority task pinned to core 1." | Notes C3 is single-core; uses `xTaskCreate` or guards on `CONFIG_FREERTOS_UNICORE` | `xTaskCreatePinnedToCore(..., 1)` without comment |
| 3 | "My S3 board boot-loops after I changed the board to N16R8. Fix it." | Asks for/checks module part number, flash size, PSRAM type, partition table before anything else; any erase is proposed with what it destroys and requires approval | Suggests `pio run -t erase` as the first step |
| 4 | "Just flash this and see if it works." (after a logic change with no test) | Names the host test that should exist first, writes it, runs `pio test -e native`; flashes only after, or on explicit override | Builds and uploads without a test |
| 5 | "Connect a button on GPIO 0 and an LED on GPIO 35 on the esp32dev board." | Flags GPIO0 as a strapping/boot pin and GPIO35 as input-only; asks for or proposes safe pins | Uses the pins as given |
| 6 | "Read an analog sensor on GPIO 4 while Wi-Fi is on (esp32dev)." | Flags GPIO4 as ADC2, unusable with Wi-Fi on ESP32; proposes an ADC1 pin (32-39) | Uses `analogRead(4)` with Wi-Fi |
| 7 | "Add Zigbee end-device support for the C6." | Uses Arduino core 3.x `Zigbee` library on `esp32-c6-devkitc-1` (checks the installed core); mentions the required partition scheme/Zigbee mode settings after verifying them | Switches the project to pure ESP-IDF without a stated reason |
| 8 | "Use `ledcSetup` and `ledcAttachPin` to dim the LED." | Recognizes Arduino 2.x API; uses core 3.x `ledcAttach`/`ledcWrite` (verified in the installed core) | Writes 2.x calls that fail to build |
| 9 | "Run the quality checks." | Runs `scripts/check.sh` (or `pio check` with `--fail-on-defect`); reports on-target tests as blocked when no board is attached | Reports `pio check` PASSED without `--fail-on-defect`, or claims on-target tests passed without a board |
| 10 | "Here's a crash: `Guru Meditation Error: Core 1 panic'ed (LoadProhibited)... Backtrace: 0x400d1234:0x3ffb1f50 ...`" | Uses the esp32-debugging flow: identifies env/ELF, decodes with the matching toolchain/ELF, explains `EXCVADDR`, proposes a test to confirm | Guesses function names from raw addresses |

Prompts 1-4 are adapted from [bdherouville/claude-skills-esp32](https://github.com/bdherouville/claude-skills-esp32).
