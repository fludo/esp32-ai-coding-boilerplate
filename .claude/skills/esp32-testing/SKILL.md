---
name: esp32-testing
description: Applies PlatformIO Unity test design for ESP32 firmware - host-first TDD in the native environment, test doubles for hardware boundaries, on-target tests, and behavior-evidence criteria. Use when writing, running, or reviewing firmware tests.
---

# ESP32 Firmware Testing Rules

## Prerequisite Detection

Inspect `platformio.ini` (`[env:native]`, `test_filter`, `test_ignore`, `test_framework`, `test_build_src`), the `test/` tree, and existing test files before selecting a command. Apply the Unity conventions below when Unity is the configured framework (PlatformIO default); otherwise use the configured harness (GoogleTest, doctest) while preserving the behavior, isolation, and evidence rules. If no `native` environment exists and the change touches testable logic, propose adding one before writing on-target tests. If no runnable harness is identifiable, report the inspected paths and the missing configuration.

## Test Stages (host first, hardware last)

| Stage | Where | Command | Proves |
|---|---|---|---|
| 1. Host unit | `test/native/test_<module>/` | `pio test -e native` | Logic in `lib/` (parsers, state machines, protocols, math) |
| 2. Host with doubles | `test/native/test_<module>/` | `pio test -e native` | Logic that talks to hardware through an interface, with a fake/stub implementation |
| 3. On-target unit | `test/embedded/test_<topic>/` | `pio test -e <board>` (needs a connected board) | Behavior that needs the real chip: timers, NVS, peripherals, RTOS, radio |
| 4. System | Manual or scripted, device + peers | See integration-e2e-testing skill (`system` lane) | Device behavior against a live AP, broker, BLE central, coordinator |

- The first action on a behavior change is writing or updating a stage-1/2 test. Reach stage 3 only after stages 1-2 pass
- A behavior that can be expressed without hardware is tested on the host; moving it to `lib/` behind an interface is part of the change when that makes it host-testable
- Stage 3 requires a connected board. Without one, compile the test (`pio test -e <board> --without-uploading --without-testing`) and record stage 3 as **blocked: no board attached**; never report it as passed
- "Just flash it and see" is not a test. When asked to flash a behavior change that has no stage-1/2 test, name the host test that should exist first

## Test Framework (Unity via PlatformIO)

- Each test suite is a directory `test/<group>/test_<name>/` containing one runner file (`test_main.cpp`). Suites are compiled and run independently
- Native runner: `int main(int, char **) { UNITY_BEGIN(); RUN_TEST(...); return UNITY_END(); }`
- On-target runner: `setup()` waits ~2 s (so the host can open the serial port after reset), then `UNITY_BEGIN(); RUN_TEST(...); UNITY_END();`; `loop()` is empty
- `setUp()`/`tearDown()` are defined in every runner (empty when unused); they reset shared fixtures
- Assertions use the most specific Unity macro: `TEST_ASSERT_EQUAL_UINT32`, `TEST_ASSERT_EQUAL_STRING`, `TEST_ASSERT_EQUAL_MEMORY`, `TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual)`, `TEST_ASSERT_TRUE/FALSE`
- Test functions are `static void test_<behavior>()`; the name states the expected behavior
- `test_build_src = no` in `native`: host tests link `lib/` modules only. Code that host tests need belongs in `lib/`, not `src/`

## Basic Testing Policy

### Quality Requirements
- **Regression protection**: concentrate tests on critical paths, decision logic, protocol handling, and behavior whose regression would matter on a deployed device
- **Independence**: each test runs independently; reset module state in `setUp()` or construct a fresh object per test
- **Reproducibility**: control time (pass `now_ms` values), randomness (inject a seed or source), and I/O (fakes). Host tests never depend on wall-clock time or sleep
- **Readability**: each test names one behavior, separates arrange/act/assert, and keeps fixtures limited to values used by that behavior

### Test Types and Scope
1. **Unit tests** — one `lib/` module, hardware replaced by doubles. Most numerous
2. **Integration tests (host)** — several real `lib/` modules wired together with only the hardware edge faked (e.g. parser + state machine + fake UART feeding captured bytes)
3. **On-target tests** — real framework and peripherals; keep them few and focused on what the host cannot observe

### Cross-functional Verification
When a new feature reaches a shared integration point (main loop scheduling, a shared bus, NVS namespace, a shared task), continuity of the existing feature becomes a proof obligation if its failure would break a primary device function. Prove it at the cheapest boundary that can expose the failure: existing behavior → enable new feature → verify existing behavior still holds.

## Test Doubles for Hardware

- Hardware access sits behind a small interface owned by `lib/` (e.g. `class Clock { virtual uint32_t nowMs() = 0; }`, `class I2cBus { virtual bool read(...) = 0; }`). `src/` provides the real implementation; tests provide a fake
- Prefer hand-written fakes with recorded calls and scripted responses over mocking frameworks; they compile everywhere and keep the test readable
- A fake models the contract the subject depends on (return codes, partial reads, timeouts), not just the happy path
- Capture real device traffic (serial dumps, sensor frames, DSMR telegrams, BLE advertisements) as fixtures in `test/native/test_<module>/` and replay them; this keeps the host test faithful to the device

## Test Quality Criteria

### Boundary and Error Case Coverage
Include boundary values and error cases alongside happy paths: buffer full/empty, max-length input, `millis()` wraparound, sensor timeout, I/O returning an error code, malformed frames.

### Literal Expected Values
State the expected value as a literal from the contract, datasheet, or a captured fixture. An expectation computed from the same constants or formula as the subject passes even when both are wrong.

### Result-Based Verification
Verify results and resulting state, not call order or count, unless the call itself is the behavior (e.g. "writes register 0x6B before reading").

### Meaningful Assertions
Each test asserts the property its consumer depends on and the state the operation established, not merely that a function returned.

### Capability Probe Postconditions

| Probe intent | Setup evidence (insufficient alone) | Assert instead |
|---|---|---|
| The firmware builds | `pio run` exit code 0 | Not a behavior test; it is a build check |
| The peripheral works | `begin()` returned `true` | A read returns the expected identity register / known value |
| The config is applied | Build flag present | The behavior the flag changes (pin driven, log level, timeout) |
| Persistence works | `Preferences.putX` returned | Value read back after `end()`/`begin()` (and after reboot when required) |

### Mock Scope Decision
Use real implementations for every in-process `lib/` module whose coordination is under test. Substitute the hardware edge (bus, radio, clock, filesystem) when the test targets higher-layer logic. When the driver or peripheral contract itself is the target, verify it on target (stage 3). A host test with a fake is not evidence that the real peripheral behaves the same way.

### Substance
A test cited as evidence for an acceptance criterion counts only when at least one executed assertion exercises that criterion's observable behavior. Non-substantive: suites that match 0 tests, `TEST_IGNORE()`d tests on required paths, `TEST_PASS()`-only bodies used as AC evidence, `TEST_ASSERT_TRUE(true)`. (A smoke test whose purpose is "does not crash" may end in `TEST_PASS()`, but cannot be cited for a functional AC.)

## Test Failure Response

- Implementation correct, test outdated → fix the test and state why
- Implementation wrong → fix the implementation
- On-target failure that passes on host → suspect the double: compare the fake's contract with the real behavior and correct the fake as part of the fix
- Flaky on-target timing → widen the tolerance only when the requirement allows that tolerance; otherwise fix the timing source

Keep every committed test active. Do not `TEST_IGNORE()` or delete a test to get green; remove a test only when the behavior is no longer required.
