// Pixy control deck -- runs on the UNO Q's STM32U585.
//
// This half exists because quadrature decoding and debounce need a tight,
// jitter-free poll loop, which is what a microcontroller is for and what Linux
// userspace is bad at. It scans at 1 kHz, cleans everything up, and exposes a
// single RPC the Python side calls once per frame.
//
// Deliberately no game logic here. Input only.
//
// Hardware: 2x HW-040 (KY-040) encoders, 4 big tactile, 2 small tactile.
//   HW-040 VCC goes to 3V3, NOT 5V -- the UNO Q's header logic is 3.3 V.
//   The modules carry their own 10k pull-ups on CLK/DT; SW has none, so it
//   uses the internal pull-up like the plain buttons.

#include <Arduino_RouterBridge.h>

// ── Pin map ───────────────────────────────────────────────────────────────
// D0/D1 are the UART, so everything starts at D2.
constexpr int ENC1_CLK = 2,  ENC1_DT = 3,  ENC1_SW = 4;
constexpr int ENC2_CLK = A2, ENC2_DT = A3, ENC2_SW = A4;  // moved off D5/D6/D7
constexpr int BTN_UP   = 8,  BTN_DOWN = 9, BTN_LEFT = 10, BTN_RIGHT = 11;
constexpr int BTN_A    = 12, BTN_B   = A5;   // moved off A1; NOT D13, see note
constexpr int BUZZER   = A0;
// D13 is deliberately unused. It drives the onboard LED, whose series resistor
// to ground divides against the ~40k internal pull-up and holds the pin below
// threshold -- a button there reads as permanently pressed.

// Bit positions in the packed reply. Python mirrors this order exactly.
enum : uint8_t {
  BIT_UP = 0, BIT_DOWN, BIT_LEFT, BIT_RIGHT,
  BIT_A, BIT_B, BIT_START, BIT_SELECT
};
constexpr int BTN_PIN[8] = {
  BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT,
  BTN_A, BTN_B, ENC1_SW, ENC2_SW      // encoder pushes are Start and Select
};

constexpr uint32_t SCAN_INTERVAL_US = 1000;   // 1 kHz
constexpr uint16_t DEBOUNCE_MS      = 8;
constexpr int8_t   DETENT_STEPS     = 4;      // HW-040 emits 4 transitions/detent

// ── Debounced button state ────────────────────────────────────────────────
struct Button {
  uint8_t  stable   = 1;   // 1 = released (pull-up), 0 = pressed
  uint8_t  reading  = 1;
  uint32_t changed  = 0;
};
static Button buttons[8];

static volatile uint8_t btnHeld    = 0;   // currently down
static volatile uint8_t btnPressed = 0;   // went down since last poll -- sticky

// ── Quadrature ────────────────────────────────────────────────────────────
// The 16-entry transition table. Counting edges instead of using this is the
// classic mistake: a cheap detented encoder bounces, and naive counting turns
// that bounce into phantom counts in both directions. Illegal transitions map
// to 0 here, so bounce contributes nothing.
static const int8_t QTAB[16] = {
   0, -1,  1,  0,
   1,  0,  0, -1,
  -1,  0,  0,  1,
   0,  1, -1,  0
};

struct Encoder {
  int pinA, pinB;
  uint8_t  prev = 0;
  int8_t   quarter = 0;             // sub-detent accumulator
  volatile int16_t detents = 0;     // whole detents since last poll
};
static Encoder enc[2] = {
  { ENC1_CLK, ENC1_DT },
  { ENC2_CLK, ENC2_DT }
};

static void scanEncoder(Encoder &e) {
  uint8_t now = (digitalRead(e.pinA) << 1) | digitalRead(e.pinB);
  if (now == e.prev) return;

  e.quarter += QTAB[(e.prev << 2) | now];
  e.prev = now;

  // Only report whole detents, so one physical click is always one step.
  while (e.quarter >= DETENT_STEPS)  { e.quarter -= DETENT_STEPS; e.detents++; }
  while (e.quarter <= -DETENT_STEPS) { e.quarter += DETENT_STEPS; e.detents--; }
}

static void scanButtons(uint32_t nowMs) {
  for (uint8_t i = 0; i < 8; i++) {
    uint8_t raw = digitalRead(BTN_PIN[i]);
    Button &b = buttons[i];

    if (raw != b.reading) {          // bouncing -- restart the settle window
      b.reading = raw;
      b.changed = nowMs;
      continue;
    }
    if (raw == b.stable) continue;
    if (nowMs - b.changed < DEBOUNCE_MS) continue;

    b.stable = raw;
    if (raw == 0) {                  // active low: a press
      btnHeld    |= (1 << i);
      btnPressed |= (1 << i);        // latched so a tap between polls survives
    } else {
      btnHeld    &= ~(1 << i);
    }
  }
}

// ── The one RPC the Linux side calls ──────────────────────────────────────
// Everything is packed into a single int32 rather than a msgpack array: it is
// one value with no composite-type surprises, and it is plenty of room.
//
//   bits  0-7   buttons currently held
//   bits  8-15  buttons pressed since last poll (cleared on read)
//   bits 16-23  encoder 1 delta, signed int8
//   bits 24-31  encoder 2 delta, signed int8
static int32_t pollInput() {
  uint8_t held, pressed;
  int16_t d0, d1;

  // Short critical section: the bridge callback runs on its own Zephyr thread,
  // so without this a poll can land mid-update and lose a press.
  noInterrupts();
  held    = btnHeld;
  pressed = btnPressed;
  btnPressed = 0;
  d0 = enc[0].detents; enc[0].detents = 0;
  d1 = enc[1].detents; enc[1].detents = 0;
  interrupts();

  if (d0 >  127) d0 =  127;  if (d0 < -127) d0 = -127;
  if (d1 >  127) d1 =  127;  if (d1 < -127) d1 = -127;

  return  (uint32_t)held
       | ((uint32_t)pressed      << 8)
       | ((uint32_t)(uint8_t)d0  << 16)
       | ((uint32_t)(uint8_t)d1  << 24);
}

// Raw pin levels, for diagnosing wiring without anyone having to press
// anything at the right moment. Bit order matches RAW_PINS below.
//
// Useful trick for the HW-040 modules: they carry 10k pull-ups to their own
// VCC. If a module's VCC leg is disconnected, those 10k resistors pull toward
// 0 V and beat the MCU's ~40k internal pull-up, so CLK/DT read LOW at rest.
// A powered, idle module reads HIGH. That distinguishes "module unpowered"
// from "module fine, signal wire off".
static const int RAW_PINS[12] = {
  ENC1_CLK, ENC1_DT, ENC1_SW, ENC2_CLK, ENC2_DT, ENC2_SW,
  BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_A, BTN_B
};
static int32_t rawPins() {
  int32_t v = 0;
  for (uint8_t i = 0; i < 12; i++) v |= (digitalRead(RAW_PINS[i]) ? 1L : 0L) << i;
  return v;
}

// Short blip. Passive buzzer only -- an active buzzer ignores the frequency.
static void beep(int freq, int ms) {
  tone(BUZZER, freq, ms);
}

void setup() {
  for (uint8_t i = 0; i < 8; i++) pinMode(BTN_PIN[i], INPUT_PULLUP);
  pinMode(ENC1_CLK, INPUT_PULLUP); pinMode(ENC1_DT, INPUT_PULLUP);
  pinMode(ENC2_CLK, INPUT_PULLUP); pinMode(ENC2_DT, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);

  for (auto &e : enc) e.prev = (digitalRead(e.pinA) << 1) | digitalRead(e.pinB);

  Bridge.begin();
  Bridge.provide("poll_input", pollInput);
  Bridge.provide("beep", beep);
  Bridge.provide("raw_pins", rawPins);

  Monitor.begin(115200);
  Monitor.println("pixy control deck ready");
}

void loop() {
  static uint32_t nextScan = 0;
  uint32_t nowUs = micros();
  if ((int32_t)(nowUs - nextScan) < 0) return;
  nextScan = nowUs + SCAN_INTERVAL_US;

  uint32_t nowMs = millis();
  scanEncoder(enc[0]);
  scanEncoder(enc[1]);
  scanButtons(nowMs);
}
