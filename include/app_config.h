#pragma once

// Project-wide defaults. Override per board in platformio.ini with
// `build_flags = -D APP_...=<value>`.

// GPIO driving the status LED. Defaults to the board variant's LED_BUILTIN
// (on RGB boards this is RGB_BUILTIN, which digitalWrite() drives in Arduino 3.x).
#ifndef APP_LED_PIN
#ifdef LED_BUILTIN
#define APP_LED_PIN LED_BUILTIN
#else
// cppcheck skips framework packages, so it never sees the variant's LED_BUILTIN.
// cppcheck-suppress preprocessorErrorDirective
#error "No LED pin known for this board: add -D APP_LED_PIN=<gpio> to its environment"
#endif
#endif

#ifndef APP_BLINK_ON_MS
#define APP_BLINK_ON_MS 100
#endif

#ifndef APP_BLINK_OFF_MS
#define APP_BLINK_OFF_MS 900
#endif
