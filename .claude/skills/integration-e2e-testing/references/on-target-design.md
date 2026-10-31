# On-Target Test Design (Hardware in the Loop)

## When to Create On-Target Tests

### Candidate Properties

An on-target candidate has all of:
- the behavior depends on the real chip, framework, or peripheral (timer resolution, RTOS scheduling, NVS/flash, GPIO/ADC/I2C/SPI/UART, sleep/wake, heap/stack limits)
- the failure cannot be reproduced on the host with a faithful fake
- the test can run unattended on one board with on-board parts or simple loopback wiring declared in the test header

### Selection Criteria

- Prefer one focused suite per hardware concern over one large suite
- Do not re-test host-tested logic on target; on target, test the adapter and the integration with the real peripheral
- Persistence across reboot needs a two-phase test (write, `ESP.restart()`, verify in the next boot) or an explicit manual step; state which
- Timing assertions state a tolerance derived from the requirement (e.g. ±5 ms), never zero

## Candidate Record

| AC | Hardware dependency | Wiring / setup | Observable result | Tolerance | Env(s) |
|----|--------------------|----------------|-------------------|-----------|--------|
| AC2 | ADC1 + reference divider | GPIO34 ↔ divider midpoint | Reading within 1.60–1.70 V | ±50 mV | esp32dev |

## Runner Structure

```cpp
#include <Arduino.h>
#include <unity.h>

void setUp() {}     // reconfigure peripherals touched by the previous test
void tearDown() {}  // release pins/peripherals, erase test NVS namespace

static void test_<behavior>() { /* arrange, act, assert */ }

void setup() {
  delay(2000);  // host opens the serial port after reset
  UNITY_BEGIN();
  RUN_TEST(test_<behavior>);
  UNITY_END();
}
void loop() {}
```

- Use a dedicated NVS namespace (`"test"`) and clear it in `tearDown`; never touch the application namespace
- Wiring requirements go in a comment block at the top of the runner and in the candidate record
- Native-USB boards (`ARDUINO_USB_CDC_ON_BOOT=1`) re-enumerate on reset; keep the startup delay and, if the runner misses output, set `test_port`/`upload_port` explicitly for that environment

## Execution

- `pio test -e <env> -f embedded/test_<feature>` runs one suite on an attached board
- Without a board: `pio test -e <env> --without-uploading --without-testing` proves only that the suite compiles; report on-target execution as blocked
- For multi-board projects, run each suite on every environment whose chip changes the behavior (e.g. single- vs dual-core, ADC differences)

## Minimal Set Check

Before finalizing, remove any on-target test whose failure would also fail a host test with the same assertion; keep it only when it adds a hardware-specific failure mode.
