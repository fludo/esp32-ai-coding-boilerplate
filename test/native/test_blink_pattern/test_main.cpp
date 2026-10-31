#include <unity.h>

#include "blink_pattern.h"

void setUp() {}
void tearDown() {}

static void test_starts_on() {
  BlinkPattern pattern(100, 900);
  pattern.start(0);
  TEST_ASSERT_TRUE(pattern.update(0));
  TEST_ASSERT_TRUE(pattern.update(99));
}

static void test_turns_off_after_on_duration() {
  BlinkPattern pattern(100, 900);
  pattern.start(0);
  TEST_ASSERT_FALSE(pattern.update(100));
  TEST_ASSERT_FALSE(pattern.update(999));
}

static void test_turns_on_again_after_full_period() {
  BlinkPattern pattern(100, 900);
  pattern.start(0);
  pattern.update(100);
  TEST_ASSERT_TRUE(pattern.update(1000));
}

static void test_catches_up_after_missed_updates() {
  BlinkPattern pattern(100, 900);
  pattern.start(0);
  // 2050 ms = two full periods + 50 ms into the third "on" phase
  TEST_ASSERT_TRUE(pattern.update(2050));
  TEST_ASSERT_FALSE(pattern.update(2100));
}

static void test_survives_millis_wraparound() {
  BlinkPattern pattern(100, 900);
  const uint32_t start = 0xFFFFFFF0u;  // 16 ms before wraparound
  pattern.start(start);
  TEST_ASSERT_TRUE(pattern.update(start + 50));  // wraps to 34
  TEST_ASSERT_FALSE(pattern.update(start + 100));
}

static void test_first_update_without_start_begins_on() {
  BlinkPattern pattern(100, 900);
  TEST_ASSERT_TRUE(pattern.update(5000));
  TEST_ASSERT_FALSE(pattern.update(5100));
}

int main(int, char **) {
  UNITY_BEGIN();
  RUN_TEST(test_starts_on);
  RUN_TEST(test_turns_off_after_on_duration);
  RUN_TEST(test_turns_on_again_after_full_period);
  RUN_TEST(test_catches_up_after_missed_updates);
  RUN_TEST(test_survives_millis_wraparound);
  RUN_TEST(test_first_update_without_start_begins_on);
  return UNITY_END();
}
