// Slow, unambiguous diagnostic. Every stage is a flat image held for seconds,
// so it can be described precisely -- unlike scrolling text, where a timing
// fault and a wiring fault look the same.

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

#define PANEL_W     64
#define PANEL_H     32
#define PANEL_CHAIN 1

#define P_R1   1
#define P_G1   2
#define P_B1   3
#define P_R2   4
#define P_G2   5
#define P_B2   6
#define P_A   43
#define P_B   41   // MTDI rear pad -- wired to panel B
#define P_C   40
#define P_D   44   // D7 -- wired to panel D
#define P_E   -1
#define P_CLK  7
#define P_LAT  8
#define P_OE   9

MatrixPanel_I2S_DMA *display = nullptr;

void hold(uint16_t colour, int ms) {
  display->fillScreen(colour);
  delay(ms);
}

void setup() {
  HUB75_I2S_CFG::i2s_pins pins = {
    P_R1, P_G1, P_B1, P_R2, P_G2, P_B2,
    P_A, P_B, P_C, P_D, P_E,
    P_LAT, P_OE, P_CLK
  };
  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);
  mxconfig.clkphase = false;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) return;
  display->setBrightness8(40);
  display->clearScreen();
}

void loop() {
  // Stage 1: flat colour fills. No addressing subtlety, no timing edge cases.
  // If these are not clean and uniform, the fault is CLK/LAT/OE or the
  // connector, not the address lines.
  hold(display->color565(255, 0, 0), 2500);   // all red
  hold(display->color565(0, 255, 0), 2500);   // all green
  hold(display->color565(0, 0, 255), 2500);   // all blue
  hold(display->color565(255, 255, 255), 2500);

  // Stage 2: the two data groups, separated. Upper half is driven by
  // R1/G1/B1, lower half by R2/G2/B2. Should be a clean split at row 16.
  display->clearScreen();
  display->fillRect(0, 0, PANEL_W, 16, display->color565(255, 0, 0));
  display->fillRect(0, 16, PANEL_W, 16, display->color565(0, 0, 255));
  delay(4000);

  // Stage 3: one row at a time, slowly. A clean single line stepping evenly
  // down the panel means the address lines are right. Jumping, doubling or
  // skipping rows means A/B/C/D are wrong -- suspect the soldered pads.
  for (int y = 0; y < PANEL_H; y++) {
    display->clearScreen();
    display->drawFastHLine(0, y, PANEL_W, display->color565(255, 255, 255));
    delay(250);
  }
}
