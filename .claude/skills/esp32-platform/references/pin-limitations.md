# ESP32-Family Pin Limitations

Use when choosing pins, adding a peripheral, or diagnosing "cannot flash", "random download mode", "ADC read fails with Wi-Fi", "pin won't drive output", "USB serial disappeared".

> **Source of truth**: [`chips/<target>.json`](chips/) — per-chip facts with links to the Espressif datasheet / ESP-IDF pages they came from. The table below summarises them; if anything disagrees with the JSON or the current datasheet, the datasheet wins. Board-level facts (which pins are broken out, what is wired to an LED/button/USB) come from the board's schematic or `variants/<variant>/pins_arduino.h`.
>
> Adapted from [esp32-claude-workbench](https://github.com/agodianel/esp32-claude-workbench) (MIT) — see `THIRD_PARTY_NOTICES.md`.

## Symptoms → Likely Pin Cause

| Symptom | Check |
|---------|-------|
| Board enters download mode or won't boot with a peripheral attached | Strapping pin held at the wrong level at reset |
| Flash / PSRAM errors, instant crash on boot | Code touches flash or PSRAM pins |
| Output pin never changes level | Input-only pin (ESP32 GPIO34-39, ESP32-S2 GPIO46) |
| USB serial/console disappears after init | USB D-/D+ pins reconfigured as GPIO |
| No boot log / can't flash over UART | UART0 console pins reused |
| ADC2 reads fail or return errors with Wi-Fi | ADC2/Wi-Fi interaction (below) |
| JTAG debugging unavailable | JTAG pins reused, or JTAG routed to USB-Serial-JTAG |

## Per-Chip Summary

| Target | Arch / cores | Flash pins (never use) | Input-only | USB D-/D+ | UART0 TX/RX | Boot-mode strapping |
|--------|------|------------------------|------------|-----------|-------------|---------------------|
| esp32 | Xtensa / 2 | 6-11 | 34-39 | — | 1 / 3 | 0, 2 (plus 5, 12, 15) |
| esp32s2 | Xtensa / 1 | 27-32 (26 = PSRAM CS) | 46 | 19 / 20 (USB OTG) | 43 / 44 | 0, 46 (45 = VDD_SPI) |
| esp32s3 | Xtensa / 2 | 27-32 (26 = PSRAM CS; 33-37 with octal flash/PSRAM) | none | 19 / 20 | 43 / 44 | 0, 46 (45 = VDD_SPI, 3 = JTAG select) |
| esp32c2 | RISC-V / 1 | 11-17 | none | — | 20 / 19 | 8, 9 |
| esp32c3 | RISC-V / 1 | 12-17 | none | 18 / 19 | 21 / 20 | 2, 8, 9 |
| esp32c5 | RISC-V / 1 | 15-22 | none | 13 / 14 | 11 / 12 | 26, 27, 28 (+ others) |
| esp32c6 | RISC-V / 1 (+LP core) | 24-30 | none | 12 / 13 | 16 / 17 | 8, 9 (4, 5, 15 also strapping) |
| esp32h2 | RISC-V / 1 | 15-21 | none | 26 / 27 | 24 / 23 | 8, 9 (25 = JTAG select) |
| esp32p4 | RISC-V / 2 | none in the GPIO range | none | 24 / 25 | 37 / 38 | 35, 36 (34, 37, 38 also strapping) |

Read the chip JSON for full strapping semantics, JTAG pins, ADC channel maps, PSRAM conditions and notes.

## ADC2 and Wi-Fi

| Chip | Behaviour | Action |
|------|-----------|--------|
| ESP32 | ADC2 pins cannot be used while Wi-Fi is used | Use ADC1 (GPIO32-39) for any analog input in a Wi-Fi product |
| ESP32-S2, ESP32-S3 | ADC2 is shared with Wi-Fi; reads can fail while Wi-Fi holds ADC2 | Prefer ADC1; if ADC2 is unavoidable, handle the error and retry |
| Others | C2, C5, C6, H2 have no ADC2; C3 has one ADC2 channel (GPIO5) that current ESP-IDF no longer supports for oneshot reads (errata) — treat ADC2 use on C3 as an error; H2/P4 have no Wi-Fi | — |

## ESP32 (classic) Details

- **Input-only**: GPIO34, 35, 36 (VP), 37, 38, 39 (VN) — no output, no internal pull-up/down. Use external resistors for buttons
- **Strapping**: GPIO0 (pull-up) + GPIO2 (pull-down): both low at reset enters download mode. GPIO12 (MTDI) selects flash voltage — pulled high on a 3.3 V-flash module → boot failure. GPIO15 (MTDO) controls ROM boot log; GPIO5 + GPIO15 SDIO timing
- **JTAG**: GPIO12-15
- **ADC1**: GPIO32-39. **ADC2**: GPIO0, 2, 4, 12-15, 25-27
- **WROVER / PSRAM modules**: GPIO16 (PSRAM CS) and normally GPIO17 (PSRAM clock) are taken

## Pin Checklist

- [ ] Target chip and module variant confirmed (board JSON, module part number: flash/PSRAM type)
- [ ] No flash or PSRAM pins used
- [ ] Outputs not on input-only pins
- [ ] Strapping pins unused, or verified safe at reset with the attached circuit
- [ ] USB D-/D+ and UART0 console pins left alone unless the console is moved
- [ ] Analog inputs on ADC1 when Wi-Fi is used (or ADC2 errors handled on S2/S3)
- [ ] JTAG pins free if hardware debugging is required
- [ ] Every pin comes from a build flag / `app_config.h` default, not a literal in logic
