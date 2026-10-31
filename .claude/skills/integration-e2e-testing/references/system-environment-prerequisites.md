# System-Lane Environment Prerequisites

System tests exercise the device against live peers. They are only as reproducible as the environment, so the Design Doc names each prerequisite and how it is provided.

## Peers and How to Provide Them

| Peer | Controlled stand-in (preferred) | Notes |
|------|-------------------------------|-------|
| Wi-Fi AP | Dedicated test AP / phone hotspot with known SSID; for loss tests, an AP that can be switched off | Never use production credentials; inject via `${sysenv.*}` or the test NVS namespace |
| MQTT broker | Local Mosquitto (`docker run eclipse-mosquitto`) with a test topic prefix | Assert with `mosquitto_sub -C <n> -W <timeout>`; the device's client ID is unique per run |
| HTTP/OTA server | `python3 -m http.server` serving the built `firmware.bin` | OTA tests need an OTA-capable partition table; record the previous firmware version |
| BLE central | `bleak` script on the host, or nRF Connect for manual steps | Clear bonds before pairing tests |
| Zigbee/Thread coordinator | A dedicated coordinator (Zigbee2MQTT test instance, OTBR) | Factory-reset the device's network state between runs; this wipes its pairing — state it |
| Sensors / actuators | A fixed rig with known reference values | Document the reference and tolerance |

## Device State

- Start from a known firmware build (record git SHA and `pio run` env) and a known NVS state
- When a test needs a clean NVS, erase **only the test namespace** from firmware; a full `erase_flash` destroys provisioning and needs explicit approval
- Capture the serial log for the whole run (`pio device monitor -e <env> --filter time --filter esp32_exception_decoder | tee tmp/<test>.log`)

## Environment Checklist

- [ ] Board attached and identified (`pio device list`), correct environment selected
- [ ] Every peer in `@dependency` reachable, with versions recorded
- [ ] Test credentials provided outside tracked files
- [ ] Device state reset procedure stated and non-destructive (or approved)
- [ ] Pass/fail observable defined at the peer (message received, state reported), not only in device logs
- [ ] Timeouts and retry counts bounded; RF-dependent results state the tolerance or are marked manual
