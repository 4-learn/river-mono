#include <Adafruit_NeoPixel.h>

#define LED_PIN   5
#define LED_COUNT 60

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.show();
  strip.setBrightness(0);  // 從全暗開始
  randomSeed(analogRead(0));
}

void loop() {

  // 每次呼吸都是新的隨機顏色
  uint8_t r = random(0, 256);
  uint8_t g = random(0, 256);
  uint8_t b = random(0, 256);

  // ----- 呼吸：漸亮 -----
  for (int brightness = 0; brightness <= 255; brightness++) {
    strip.setBrightness(brightness);
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
    delay(5);  // 控制呼吸速度
  }

  // ----- 呼吸：漸暗 -----
  for (int brightness = 255; brightness >= 0; brightness--) {
    strip.setBrightness(brightness);
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
    delay(5);
  }

}
