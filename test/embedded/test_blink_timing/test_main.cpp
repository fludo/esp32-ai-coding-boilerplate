// On-target test: runs on the board with `pio test -e <board>`.
// Verifies the pattern against the real millis() clock and that the LED pin
// accepts output writes on this board.
#include <Arduino.h>
#include <unity.h>

#include "app_config.h"
#include "blink_pattern.h"

void setUp() {}
void tearDown() {}

static void test_pattern_follows_real_clock() {
  BlinkPattern pattern(50, 50);
  const uint32_t start = millis();
  pattern.start(start);
  TEST_ASSERT_TRUE(pattern.update(millis()));
  delay(60);
  TEST_ASSERT_FALSE(pattern.update(millis()));
  delay(50);
  TEST_ASSERT_TRUE(pattern.update(millis()));
}

static void test_led_pin_toggles_without_fault() {
  pinMode(APP_LED_PIN, OUTPUT);
  for (int i = 0; i < 4; ++i) {
    digitalWrite(APP_LED_PIN, (i % 2) ? LOW : HIGH);
    delay(100);
  }
  digitalWrite(APP_LED_PIN, LOW);
  TEST_PASS();
}

void setup() {
  delay(2000);  // give the host time to open the serial port after reset
  UNITY_BEGIN();
  RUN_TEST(test_pattern_follows_real_clock);
  RUN_TEST(test_led_pin_toggles_without_fault);
  UNITY_END();
}

void loop() {}
