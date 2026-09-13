// Panel receiver over WiFi, for the UNO Q project.
//
// Same dumb-display role as the USB version: it owns the HUB75 refresh and
// nothing else. The UNO Q renders every frame in Python and streams finished
// RGB565 over TCP.
//
// TCP rather than UDP on purpose -- a frame is 4096 bytes, well past the ~1472
// byte UDP payload limit, so UDP would mean writing fragmentation and
// reassembly by hand. TCP already does it, and 4KB a frame is nowhere near
// saturating the link.
//
// Wire protocol is unchanged from the serial build:
//   0xA5 0x5A <cmd> <len:uint16 LE> <payload...>
//     0x01 frame (4096 bytes RGB565, big endian per pixel)
//     0x02 brightness (1 byte)
//     0x03 clear
//     0x04 ping
//   Each handled command is acknowledged with a single 0x06 byte.

#include <WiFi.h>
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>
#include "secrets.h"

#define PANEL_W     64
#define PANEL_H     32
#define PANEL_CHAIN 1
#define TCP_PORT    3333

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
#define ACK            0x06

static const uint16_t FRAME_BYTES = PANEL_W * PANEL_H * 2;

MatrixPanel_I2S_DMA *display = nullptr;
WiFiServer server(TCP_PORT);
WiFiClient client;
static uint8_t frame[FRAME_BYTES];

static void banner(const char *l1, const char *l2, uint16_t colour) {
  display->clearScreen();
  display->setTextSize(1);
  display->setTextColor(colour);
  display->setCursor(1, 6);
  display->print(l1);
  if (l2) { display->setCursor(1, 18); display->print(l2); }
  display->flipDMABuffer();
}

// Split "192.168.1.42" across two lines so it fits 64px at the 6px base font.
static void showAddress(IPAddress ip) {
  char top[20], bottom[20];
  snprintf(top, sizeof(top), "%u.%u.", ip[0], ip[1]);
  snprintf(bottom, sizeof(bottom), "%u.%u", ip[2], ip[3]);
  banner(top, bottom, display->color565(0, 220, 255));
}

static bool readExact(uint8_t *dst, size_t want, uint32_t timeoutMs = 3000) {
  size_t got = 0;
  uint32_t deadline = millis() + timeoutMs;
  while (got < want) {
    if (millis() > deadline || !client.connected()) return false;
    int n = client.read(dst + got, want - got);
    if (n > 0) got += n;
  }
  return true;
}

static void blitFrame() {
  size_t i = 0;
  for (int y = 0; y < PANEL_H; y++) {
    for (int x = 0; x < PANEL_W; x++) {
      display->drawPixel(x, y, ((uint16_t)frame[i] << 8) | frame[i + 1]);
      i += 2;
    }
  }
  display->flipDMABuffer();
}

void setup() {
  HUB75_I2S_CFG::i2s_pins pins = {
    P_R1, P_G1, P_B1, P_R2, P_G2, P_B2,
    P_A, P_B, P_C, P_D, P_E,
    P_LAT, P_OE, P_CLK
  };
  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);
  mxconfig.clkphase    = false;
  mxconfig.double_buff = true;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) return;
  display->setBrightness8(60);
  display->clearScreen();

  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.printf("target SSID: \"%s\" (%u chars)\n", WIFI_SSID, strlen(WIFI_SSID));
  Serial.printf("pass length: %u chars\n", strlen(WIFI_PASS));

  banner("WIFI", "SCAN", display->color565(255, 180, 0));

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);          // sleep adds latency and stutters streaming
  WiFi.disconnect(true);
  delay(200);

  // Scan first: proves whether the radio can even see the target network,
  // which separates "wrong password" from "wrong band / out of range".
  int n = WiFi.scanNetworks();
  Serial.printf("scan found %d networks:\n", n);
  bool seen = false;
  for (int i = 0; i < n; i++) {
    bool match = (WiFi.SSID(i) == WIFI_SSID);
    if (match) seen = true;
    Serial.printf("  %2d %-32s ch%-3d %4d dBm %s\n", i,
                  WiFi.SSID(i).c_str(), WiFi.channel(i), WiFi.RSSI(i),
                  match ? "  <-- TARGET" : "");
  }
  Serial.printf("target visible: %s\n", seen ? "YES" : "NO");

  banner("WIFI", "...", display->color565(255, 180, 0));
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint32_t deadline = millis() + 30000;
  while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
    delay(1000);
    Serial.printf("  status=%d\n", WiFi.status());
  }

  if (WiFi.status() != WL_CONNECTED) {
    // 1=SSID not found  4=auth failed (usually a wrong password)  6=disconnected
    Serial.printf("FAILED, final status=%d\n", WiFi.status());
    banner("WIFI", "FAIL", display->color565(255, 0, 0));
    return;
  }
  Serial.printf("connected, IP=%s RSSI=%d\n",
                WiFi.localIP().toString().c_str(), WiFi.RSSI());

  server.begin();
  server.setNoDelay(true);       // without this, Nagle batches frames and stutters
  showAddress(WiFi.localIP());   // panel shows where to connect
}

void loop() {
  if (!client || !client.connected()) {
    client = server.available();
    if (!client) { delay(5); return; }
    client.setNoDelay(true);
  }

  static uint8_t prev = 0;
  if (client.available() <= 0) return;
  uint8_t b = (uint8_t)client.read();
  if (prev != 0xA5 || b != 0x5A) { prev = b; return; }
  prev = 0;

  uint8_t header[3];
  if (!readExact(header, 3)) return;
  uint8_t  cmd = header[0];
  uint16_t len = (uint16_t)header[1] | ((uint16_t)header[2] << 8);

  switch (cmd) {
    case CMD_FRAME:
      if (len != FRAME_BYTES) return;
      if (readExact(frame, FRAME_BYTES)) { blitFrame(); client.write(ACK); }
      break;
    case CMD_BRIGHTNESS: {
      uint8_t v;
      if (len == 1 && readExact(&v, 1)) { display->setBrightness8(v); client.write(ACK); }
      break;
    }
    case CMD_CLEAR:
      display->clearScreen();
      display->flipDMABuffer();
      client.write(ACK);
      break;
    case CMD_PING:
      client.write(ACK);
      break;
  }
}
