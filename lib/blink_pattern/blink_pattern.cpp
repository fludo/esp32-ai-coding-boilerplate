#include "blink_pattern.h"

BlinkPattern::BlinkPattern(uint32_t onMs, uint32_t offMs) : onMs_(onMs), offMs_(offMs) {}

void BlinkPattern::start(uint32_t nowMs) {
  phaseStartMs_ = nowMs;
  on_ = true;
  started_ = true;
}

bool BlinkPattern::update(uint32_t nowMs) {
  if (!started_) {
    start(nowMs);
    return on_;
  }
  // Unsigned subtraction keeps the elapsed time correct across wraparound.
  // The loop catches up if update() was not called for several phases.
  uint32_t phaseMs = on_ ? onMs_ : offMs_;
  while (phaseMs > 0 && static_cast<uint32_t>(nowMs - phaseStartMs_) >= phaseMs) {
    phaseStartMs_ += phaseMs;
    on_ = !on_;
    phaseMs = on_ ? onMs_ : offMs_;
  }
  return on_;
}
