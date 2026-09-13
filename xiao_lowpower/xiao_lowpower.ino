// Minimal-current wiring check for the Waveshare 64x32 panel.
// Lights only a few dozen LEDs at very low brightness, so it has a chance of
// staying inside a USB port's ~500 mA budget. This is a WIRING test only --
// it is not how you run the panel. Use a 5V / 2.5A supply for real work.

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

#define PANEL_W     64
#define PANEL_H     32
#define PANEL_CHAIN 1

#define P_R1   1   // D0
#define P_G1   2   // D1
#define P_B1   3   // D2
#define P_R2   4   // D3
#define P_G2   5   // D4
#define P_B2   6   // D5
#define P_A   43   // D6
#define P_B   41   // MTDI rear pad -- wired to panel B
#define P_C   40   // rear pad, MTDO
#define P_D   44   // D7 -- wired to panel D
#define P_E   -1   // unused: 64x32 is 1/16 scan
#define P_CLK  7   // D8
#define P_LAT  8   // D9
#define P_OE   9   // D10

MatrixPanel_I2S_DMA *display = nullptr;

void setup() {
  Serial.begin(115200);

  HUB75_I2S_CFG::i2s_pins pins = {
    P_R1, P_G1, P_B1, P_R2, P_G2, P_B2,
    P_A, P_B, P_C, P_D, P_E,
    P_LAT, P_OE, P_CLK
  };
  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);
  mxconfig.clkphase = false;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) {
    Serial.println("DMA allocation failed");
    return;
  }
  display->setBrightness8(12);   // ~5% -- deliberately dim to limit current
  display->clearScreen();

  uint16_t white = display->color565(255, 255, 255);
  uint16_t red   = display->color565(255, 0, 0);
  uint16_t green = display->color565(0, 255, 0);
  uint16_t blue  = display->color565(0, 0, 255);

  // One pixel per row down the left edge. All 32 rows means every address
  // combination A..D gets exercised, in both the upper and lower half.
  // A gap anywhere here means an address line is miswired.
  for (int y = 0; y < PANEL_H; y++) {
    display->drawPixel(0, y, white);
  }

  // Colour check, upper half (R1/G1/B1) and lower half (R2/G2/B2).
  // Wrong colour here means the corresponding data line is swapped.
  display->drawPixel(10, 5, red);
  display->drawPixel(13, 5, green);
  display->drawPixel(16, 5, blue);
  display->drawPixel(10, 21, red);
  display->drawPixel(13, 21, green);
  display->drawPixel(16, 21, blue);
}

void loop() {
  // Nothing: a static image keeps the current draw flat and predictable.
}
