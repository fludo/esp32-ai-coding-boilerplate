#pragma once

#include <stdint.h>

// Non-blocking on/off pattern driven by an externally supplied clock.
// Framework-free so it can be unit-tested on the host (test/native/).
class BlinkPattern {
 public:
  BlinkPattern(uint32_t onMs, uint32_t offMs);

  // Starts the pattern in the "on" phase at `nowMs`.
  void start(uint32_t nowMs);

  // Advances the pattern to `nowMs` and returns whether the output is on.
  // Safe across millis() wraparound.
  bool update(uint32_t nowMs);

  bool isOn() const { return on_; }

 private:
  uint32_t onMs_;
  uint32_t offMs_;
  uint32_t phaseStartMs_ = 0;
  bool on_ = false;
  bool started_ = false;
};
