// Panel receiver for the UNO Q project.
//
// This sketch is deliberately dumb: it owns the HUB75 refresh, which needs
// hard real-time behaviour, and nothing else. All rendering -- fonts, images,
// scrolling, effects -- happens in Python on the UNO Q, which ships finished
// RGB565 frames down the wire.
//
// Wire protocol, little endian length:
//   0xA5 0x5A <cmd> <len:uint16> <payload...>
//     cmd 0x01  full frame, payload = 4096 bytes RGB565, big endian per pixel
//     cmd 0x02  brightness, payload = 1 byte (0-255)
//     cmd 0x03  clear, no payload

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

#define CMD_FRAME      0x01
#define CMD_BRIGHTNESS 0x02
#define CMD_CLEAR      0x03
#define CMD_PING       0x04

static const uint16_t FRAME_BYTES = PANEL_W * PANEL_H * 2;

MatrixPanel_I2S_DMA *display = nullptr;
static uint8_t frame[FRAME_BYTES];

// Blocking read with a deadline, so a truncated packet can't wedge the loop.
static bool readExact(uint8_t *dst, size_t want, uint32_t timeoutMs = 2000) {
  size_t got = 0;
  uint32_t deadline = millis() + timeoutMs;
  while (got < want) {
    if (millis() > deadline) return false;
    int n = Serial.readBytes(dst + got, want - got);
    if (n > 0) got += n;
  }
  return true;
}

static void blitFrame() {
  size_t i = 0;
  for (int y = 0; y < PANEL_H; y++) {
    for (int x = 0; x < PANEL_W; x++) {
      uint16_t c = ((uint16_t)frame[i] << 8) | frame[i + 1];
      display->drawPixel(x, y, c);
      i += 2;
    }
  }
  display->flipDMABuffer();   // swap in one go, so frames never tear
}

void setup() {
  // The USB CDC receive ring defaults to 256 bytes. A frame is 4096, and the
  // host sends it in one burst, so the ring overflows and the payload arrives
  // truncated. Size it to hold a whole frame with headroom. Must be called
  // before begin().
  Serial.setRxBufferSize(8192);
  Serial.begin(921600);       // ignored on USB CDC, matters on the UART fallback
  Serial.setTimeout(100);

  HUB75_I2S_CFG::i2s_pins pins = {
    P_R1, P_G1, P_B1, P_R2, P_G2, P_B2,
    P_A, P_B, P_C, P_D, P_E,
    P_LAT, P_OE, P_CLK
  };
  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);
  mxconfig.clkphase   = false;
  mxconfig.double_buff = true;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) return;
  display->setBrightness8(60);
  display->clearScreen();

  // Brief splash so it is obvious the receiver is alive and waiting.
  display->setTextColor(display->color565(0, 200, 255));
  display->setCursor(2, 12);
  display->print("READY");
  display->flipDMABuffer();
}

void loop() {
  // Hunt for the two byte preamble one byte at a time, remembering the
  // previous byte across calls. Reading both bytes in one pass would break
  // whenever 0xA5 lands at the end of a USB packet and 0x5A has not arrived
  // yet -- that loses the preamble and desynchronises the stream for good.
  static uint8_t prev = 0;
  if (Serial.available() <= 0) return;
  uint8_t b = (uint8_t)Serial.read();
  if (prev != 0xA5 || b != 0x5A) { prev = b; return; }
  prev = 0;

  uint8_t header[3];
  if (!readExact(header, 3)) return;

  uint8_t  cmd = header[0];
  uint16_t len = (uint16_t)header[1] | ((uint16_t)header[2] << 8);

  switch (cmd) {
    case CMD_FRAME:
      if (len != FRAME_BYTES) return;
      if (readExact(frame, FRAME_BYTES)) { blitFrame(); Serial.write(0x06); }
      break;

    case CMD_BRIGHTNESS: {
      uint8_t b;
      if (len == 1 && readExact(&b, 1)) { display->setBrightness8(b); Serial.write(0x06); }
      break;
    }

    case CMD_CLEAR:
      display->clearScreen();
      display->flipDMABuffer();
      Serial.write(0x06);
      break;

    case CMD_PING:
      Serial.write(0x06);
      break;
  }
}
