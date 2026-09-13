// Address-line identification.
//
// Draws four single-row lines at y = 1, 2, 4 and 8 -- each a power of two, so
// each asserts exactly ONE address bit. y=1 asserts only our A line, y=2 only
// B, y=4 only C, y=8 only D.
//
// If the lines are wired correctly they appear top to bottom as
// RED, GREEN, BLUE, WHITE. Any other order reveals the permutation directly:
// the lit rows are always physically 1, 2, 4, 8 from the top, so whichever
// colour sits topmost is the line feeding the panel's A input, and so on.

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
#define P_A   43   // D6   -> asserted alone by the RED line
#define P_B   41   // MTDI rear pad -- wired to panel B
#define P_C   40   // MTDO -> BLUE
#define P_D   44   // D7 -- wired to panel D
#define P_E   -1
#define P_CLK  7
#define P_LAT  8
#define P_OE   9

MatrixPanel_I2S_DMA *display = nullptr;

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
  display->setBrightness8(50);
  display->clearScreen();

  display->drawFastHLine(0, 1, PANEL_W, display->color565(255, 0, 0));     // A
  display->drawFastHLine(0, 2, PANEL_W, display->color565(0, 255, 0));     // B
  display->drawFastHLine(0, 4, PANEL_W, display->color565(0, 0, 255));     // C
  display->drawFastHLine(0, 8, PANEL_W, display->color565(255, 255, 255)); // D
}

void loop() {
  // Static image: nothing moves, so the order is unambiguous.
}
