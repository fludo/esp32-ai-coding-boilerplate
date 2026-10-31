---
name: integration-e2e-testing
description: Selects and designs the smallest integration / on-target / system test set that proves accepted firmware behavior at an observable boundary. Use when writing or reviewing integration, hardware-in-the-loop, or end-to-end device tests.
---

# Integration, On-Target and System Test Design Rules

## References

- **[references/on-target-design.md](references/on-target-design.md)** - on-target (hardware-in-the-loop) test design: candidate properties, selection criteria, runner structure, timing tolerance
- **[references/system-environment-prerequisites.md](references/system-environment-prerequisites.md)** - system-lane prerequisites: test peers (AP, broker, BLE central, coordinator), device state, environment checklist

## Test Types and Selection

| Lane | Purpose | Scope | External Deps | Location | Implementation Timing |
|------|---------|-------|---------------|----------|----------------------|
| `integration` | Verify module interactions on the host | Several real `lib/` modules wired together; only the hardware edge faked | Fakes for clock/bus/radio/storage | `test/native/test_<feature>_int/` | Created alongside implementation |
| `on-target` | Verify behavior that needs the real chip, deterministic and self-contained | Real framework + peripherals on one board; loopback wiring or on-board parts only | Board only — no network peers | `test/embedded/test_<feature>/` | Created alongside the feature; executed when a board is attached |
| `system` | Verify a contract only a running device with live peers can expose | Device firmware + external peers (Wi-Fi AP, MQTT broker, BLE central, Zigbee coordinator, sensor rig) | Live peers or a controlled local stand-in | `test/embedded/test_<feature>_sys/` or a scripted procedure in the Design Doc | Executed after the device and peers exist |

**Lane selection**:
- Default to the host (`integration`, or unit tests per esp32-testing) whenever the behavior is observable without hardware
- Select **on-target** for timer/RTOS behavior, NVS persistence across reboot, peripheral I/O, sleep/wake, memory/stack limits — anything the host cannot reproduce
- Select **system** only when the proof obligation is real interaction with a peer: association/reconnect, broker publish/subscribe, BLE pairing/GATT, Zigbee join/reporting, OTA from a server

Start from accepted proof obligations, assign each to the cheapest boundary that can expose its failure, remove duplicate coverage, and keep the smallest set that covers every remaining distinct failure. A feature may validly produce no test in a lane.

## Behavior-First Principle

### Candidate Evidence

A candidate states:
- an observable result at the boundary named by the accepted behavior (return value, GPIO level, serial/Unity output, NVS value, message received by the peer)
- a material failure that crosses the components exercised by the selected lane
- an automated runner or controlled environment that can reproduce the failure

Route behavior observable in isolation to unit tests. Record an unavailable board or peer as a proof prerequisite for the on-target / system lane — never as a pass.

### Candidate Routing

- Keep decision logic, data integrity, device-visible behavior, and observable error handling in the integration/on-target pool when they require those boundaries
- Route pure transformations (parsing, encoding, math) to host unit tests, timing/power claims to measured on-target verification with an explicit tolerance, and RF range/throughput claims to manual system verification

## Skeleton Specification

### Required Skeleton Format

A committed suite must compile and run in its environment. A skeleton is a Unity runner whose pending cases call `TEST_IGNORE_MESSAGE("TODO: <AC id>")`, with only the Unity include and the required comments. The implementing task replaces each pending case with arrange/act/assert, adds application includes and fakes, and removes the ignore.

Each test MUST carry these annotations as comments directly above it:

```cpp
// AC: "[Acceptance criteria original text]"
// Behavior: [Trigger] -> [Process] -> [Observable Result]
// @lane: integration | on-target | system
// @dependency: none | [module names] | board:<env> | board:<env>+[peer names]
// @real-dependency: [component] (optional, when Test Boundaries specify non-fake setup)
// Primary failure mode: [specific regression that must make the implemented test fail]
// Proof obligation: [boundary and observable state the implemented test must assert]
// Verification items: [observations that establish the obligation]
static void test_ac1_reconnects_after_ap_loss() { TEST_IGNORE_MESSAGE("TODO: AC1"); }
```

### Property Annotations

```cpp
// Property: `[invariant expression]`
// Inputs: exhaustive [range] | table [fixture name] | seeded random (seed=<n>, count=<n>)
```

Implement a property as an exhaustive loop when the domain is small (e.g. all `uint8_t`), a table of boundary cases, or a seeded pseudo-random loop that prints the seed and failing input. A discovered failing input becomes its own named unit test.

## Test Set Selection

1. Read the accepted behavior and each recorded proof obligation from the governing artifact or task.
2. For each obligation, name the material failure that must make a test fail and the observable state that exposes it.
3. Search existing tests. Reuse coverage only when it exercises the same boundary and would fail for that failure.
4. Assign the obligation to the narrowest sufficient lane:
   - unit when one module in isolation exposes the behavior
   - `integration` for multi-module contracts on the host
   - `on-target` for behavior that needs the chip but no peers
   - `system` for behavior exposed only through a live peer
5. Merge obligations when one scenario proves them while preserving a clear assertion-to-failure mapping.
6. Emit only the remaining minimal covering set, with the annotations above.

Escalate when the accepted behavior or required contract remains unresolved after consulting governing sources and repository evidence.

## Implementation Rules

### Behavior Verification Implementation

| Step Type | Verification Target | Example |
|-----------|--------------------|---------|
| Trigger | Reproduce in Arrange | Fake bus returns NACK; fake clock advanced past timeout; AP powered off |
| Process | Intermediate state or call | State machine enters `Reconnecting`; retry counter incremented |
| Observable Result | Final output | Return status, GPIO level, published message, NVS value after reboot |

**Pass Criteria**: the observable result is asserted as a return value, resulting state, value read back through the real boundary, or a call recorded by the fake when the call itself is the behavior.

### Verification Item Determination Rules

| Skeleton State | Verification Item Determination Method |
|----------------|---------------------------------------|
| `// Verification items:` listed | Implement all listed items as assertions |
| No `// Verification items:` | Derive from "Observable Result" in the Behavior line |
| Both present | Prioritize verification items, use behavior as supplement |

### Integration Test Double Boundaries

| Condition | Boundary to use |
|---|---|
| The driver, peripheral, radio, or peer contract itself is under test | The real boundary in the `on-target`/`system` lane — a fake cannot prove the contract it stands in for |
| Hardware edge not under test | Fake implementing the `lib/` interface |
| Module interaction under test | Real `lib/` modules |
| The call itself is what the test verifies (e.g. register write order, log line) | Recording fake, asserted |
| Neither the call nor its target is under test | Real, or a no-op fake |

### Execution Conditions

**on-target**: runs with `pio test -e <env>` on an attached board; without a board, compile it (`--without-uploading --without-testing`) and record execution as blocked.

**system**: runs only when the peers listed in `@dependency` are available; the Design Doc names how each peer is provided (see references). Results record firmware version, board, and peer versions.

## Review Criteria

### Skeleton and Implementation Consistency

| Check | Failure Condition |
|-------|-------------------|
| Property Verification | Property annotation exists but no exhaustive/table/seeded loop implements it |
| Behavior Verification | No assertion on the "Observable Result" |
| Verification Item Coverage | Listed verification items have no assertion |
| Double Boundary | A `lib/` module under test replaced by a fake in an integration test |
| Pending Cases | `TEST_IGNORE*` remains on an implemented AC |

### Implementation Quality

| Check | Failure Condition |
|-------|-------------------|
| AAA Structure | Arrange/Act/Assert separation unclear |
| Independence | State shared between tests (globals, NVS keys, peripherals left configured) without reset in `setUp`/`tearDown` |
| Reproducibility | Depends on wall-clock time, unseeded randomness, or RF conditions without stated tolerance |
| Timing Tolerance | On-target timing asserted with zero tolerance, or a tolerance wider than the requirement allows |

### Route Parity for Shared Mutations

When multiple routes reach the same mutation — a serial command and an MQTT command, a button press and a BLE write, a periodic task and a manual trigger — compare them along validation, classification, resource bounds, and the order of read, parse, mutation, and reporting.

A difference is permitted only by a source that decides intent: a requirement, the Design Doc, or an ADR. When a difference has no permitting source, require a test that drives the mutation through the permissive route and asserts the state the skipped check protects.

| Check | Failure Condition |
|-------|-------------------|
| Validation parity | One route validates an input the other accepts unchecked |
| Classification parity | The same failure is reported differently per route |
| Resource-bound parity | One route enforces a size, rate, or timeout bound the other omits |
| Operation-order parity | One route can mutate (or persist to NVS) before validating |
| Bypass coverage | An unexplained difference has no test driving the permissive route |
