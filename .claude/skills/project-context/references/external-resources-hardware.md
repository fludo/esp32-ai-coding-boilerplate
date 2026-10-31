# Hardware External Resource Axes

Hearing axes for firmware work: boards, wiring, peripherals, and the devices the firmware talks to.

## Axis 1: Board and Wiring Source

The canonical source for which board/module is used and what is connected to which pin.

**AskUserQuestion choices**:
- Schematic or pinout file in the repository (e.g., `docs/hardware/`, KiCad project)
- Vendor board page / pinout image (URL)
- Wiring table in project documentation
- Wiring only in `platformio.ini` build flags / `include/app_config.h`
- No documented wiring
- Not applicable

**Follow-up (when the axis is present)**: Capture two fields:
- **Location**: file path or URL, plus module part number when known (e.g., ESP32-S3-WROOM-1-N16R8)
- **Access method**: file read or WebFetch

When several boards are supported, capture each as a separate entry using the `[env:...]` name as the disambiguating suffix.

## Axis 2: Peripheral Datasheets and Protocol Specs

Datasheets for attached sensors/actuators and specifications for wire or radio protocols the firmware implements (e.g., DSMR P1, Modbus, Zigbee clusters).

**AskUserQuestion choices**:
- PDFs in the repository
- Vendor URLs
- Library documentation only (driver library in `lib_deps`)
- No external peripherals or protocols
- Not applicable

**Follow-up (when the axis is present)**: Capture two fields:
- **Location**: file path or URL per part/protocol
- **Access method**: file read or WebFetch

## Axis 3: Test Peers and Rig

What the device is tested against beyond the board itself (see integration-e2e-testing, `system` lane).

**AskUserQuestion choices**:
- Local services (MQTT broker, HTTP/OTA server, Home Assistant / Zigbee2MQTT test instance)
- Dedicated test Wi-Fi AP / coordinator / BLE central
- Physical test rig (reference sensor values, loopback wiring)
- Production systems only (no isolated test peer)
- No external peers
- Not applicable

**Follow-up (when the axis is present)**: Capture two fields:
- **Location**: host/URL or rig description
- **Access method**: CLI command (e.g., `mosquitto_sub -h <host> -t <topic>`), web UI URL, or manual procedure

## Axis 4: Device Credentials and Provisioning

How Wi-Fi credentials, broker credentials, keys, or certificates reach the device.

**AskUserQuestion choices**:
- Gitignored header (`include/secrets.h`)
- Environment variables injected at build time (`${sysenv.*}`)
- Runtime provisioning (captive portal, Improv, BLE provisioning, NVS partition image)
- No credentials required
- Not applicable

**Follow-up (when the axis is present)**: Capture two fields:
- **Location**: file path, variable names, or provisioning method
- **Access method**: how a developer obtains the values (password manager entry, team vault, manual)

Capture only how to reach the values — never the values themselves.

## Self-Declaration Phase

After the four structured axes, ask once: "Are there any other hardware or device-side external resources this project depends on beyond what the structured questions covered? List each in your next message, or reply 'none'."

Capture free-form answers under the "Additional Resources" subsection of the Hardware block. Run this phase even when every structured axis returned "Not applicable".

Examples of resources that surface only via self-declaration: logic analyzer captures, calibration data sheets, enclosure/power constraints documents, certification requirements, a companion mobile app or cloud backend owned by another repository.
