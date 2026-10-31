#include <Arduino.h>

#include "app_config.h"
#include "blink_pattern.h"

static const char *TAG = "main";

static BlinkPattern statusLed(APP_BLINK_ON_MS, APP_BLINK_OFF_MS);
static bool ledOn = false;

void setup() {
  Serial.begin(115200);
  pinMode(APP_LED_PIN, OUTPUT);
  statusLed.start(millis());
  ESP_LOGI(TAG, "%s rev %d, %d core(s), %u KB free heap", ESP.getChipModel(), ESP.getChipRevision(),
           ESP.getChipCores(), static_cast<unsigned>(ESP.getFreeHeap() / 1024));
}

void loop() {
  const bool on = statusLed.update(millis());
  if (on != ledOn) {
    digitalWrite(APP_LED_PIN, on ? HIGH : LOW);
    ledOn = on;
  }
  delay(1);
}
