// Waveshare 64x32 HUB75 panel driven by a XIAO ESP32-S3.
// Standalone hardware check: colour bars, then scrolling text, then a bitmap.

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

#define PANEL_W     64
#define PANEL_H     32
#define PANEL_CHAIN 1

// XIAO ESP32-S3 pin map.
// The eleven edge castellations carry the six colour lines, CLK/LAT/OE and
// address A/B. Address C/D come off the two rear JTAG pads -- they only
// change once per row, so the hand-soldered wires are least critical there.
#define P_R1   1   // D0
#define P_G1   2   // D1
#define P_B1   3   // D2
#define P_R2   4   // D3
#define P_G2   5   // D4
#define P_B2   6   // D5
#define P_A   43   // D6  (also UART0 TX)
#define P_B   41   // MTDI rear pad -- wired to panel B
#define P_C   40   // rear pad, MTDO
#define P_D   44   // D7 -- wired to panel D
#define P_E   -1   // unused: 64x32 is 1/16 scan
#define P_CLK  7   // D8
#define P_LAT  8   // D9
#define P_OE   9   // D10

MatrixPanel_I2S_DMA *display = nullptr;

void colourBars() {
  display->clearScreen();
  const uint16_t bars[8] = {
    display->color565(255, 255, 255), display->color565(255, 255, 0),
    display->color565(0, 255, 255),   display->color565(0, 255, 0),
    display->color565(255, 0, 255),   display->color565(255, 0, 0),
    display->color565(0, 0, 255),     display->color565(40, 40, 40),
  };
  for (int i = 0; i < 8; i++) {
    display->fillRect(i * 8, 0, 8, PANEL_H, bars[i]);
  }
}

void scrollText(const char *msg, uint16_t colour) {
  display->setTextSize(1);
  display->setTextWrap(false);
  display->setTextColor(colour);
  int width = strlen(msg) * 6;
  for (int x = PANEL_W; x > -width; x--) {
    display->clearScreen();
    display->setCursor(x, 12);
    display->print(msg);
    delay(30);
  }
}

// A 16x16 smiley, one bit per pixel, drawn scaled up in the centre.
const uint16_t smiley[16] = {
  0x07E0, 0x1818, 0x2004, 0x4002, 0x4812, 0x8811, 0x8001, 0x8001,
  0x8811, 0x8421, 0x43C2, 0x4002, 0x2004, 0x1818, 0x07E0, 0x0000,
};

void drawSmiley() {
  display->clearScreen();
  uint16_t yellow = display->color565(255, 200, 0);
  for (int row = 0; row < 16; row++) {
    for (int col = 0; col < 16; col++) {
      if (smiley[row] & (1 << (15 - col))) {
        display->drawPixel(col + 24, row + 8, yellow);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);

  HUB75_I2S_CFG::i2s_pins pins = {
    P_R1, P_G1, P_B1, P_R2, P_G2, P_B2,
    P_A, P_B, P_C, P_D, P_E,
    P_LAT, P_OE, P_CLK
  };
  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);
  mxconfig.clkphase = false;   // flip this if the image is shifted by a pixel

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) {
    Serial.println("DMA allocation failed");
    return;
  }
  display->setBrightness8(60);  // keep current draw modest while bench testing
  display->clearScreen();
}

void loop() {
  colourBars();
  delay(3000);
  scrollText("HELLO UNO Q", display->color565(0, 255, 128));
  drawSmiley();
  delay(3000);
}
