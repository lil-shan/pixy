# Pixy — a STEM learning console that runs on what you learn

> Solve real engineering puzzles on a 64×32 LED matrix, bank the Charge you
> earn, and spend it in the arcade. Built on the Arduino UNO Q, using both of
> its brains.

*[IMAGE: docs/img/shell.png — Home, Learn and Arcade menus]*

---

## The idea

Most STEM toys pick a side. Either they teach and feel like homework, or they
entertain and the learning is a thin coat of paint.

Pixy makes the learning **the power source**. Every puzzle you solve pays
*Charge*. Charge is what unlocks the arcade — Breakout, Pong, Snake, Simon. A
kid who wants to play Pong gets there by working out gear ratios, and that is
the entire design.

One decision shaped everything else: **arcade unlocks are permanent, one-time
purchases, not pay-per-play.** Charging per play turns learning into a toll
booth, and a kid who runs short simply stops. A one-time unlock gives you
something to work toward that then keeps giving.

---

## Why the Arduino UNO Q

The UNO Q has two processors — a quad-core Cortex-A53 running Debian, and an
STM32U585 microcontroller — and Pixy puts **both on the critical path**, which
is the whole argument for the board.

| Processor | Job | Why it and not the other |
|---|---|---|
| **STM32U585** | Reads the control deck at 1 kHz | Quadrature decoding and debounce need a jitter-free loop. Linux userspace has no real-time guarantee |
| **A53 / Debian** | Every game, all rendering, the Charge economy | Python and Pillow. Real fonts, real image handling, a real filesystem for save state |
| XIAO ESP32-S3 | Pixel pump for the HUB75 panel | See below |

### The one thing the UNO Q can't do alone

A HUB75 LED panel has no framebuffer and no PWM. Something must bit-bang
thirteen signals at 100+ full refreshes a second, with binary code modulation
layered on for colour depth. That needs DMA hardware or a dedicated real-time
core.

Neither half of the UNO Q has it. Linux userspace flickers, and the standard
Linux HUB75 library (`rpi-rgb-led-matrix`) pokes BCM2835 registers directly —
it is Raspberry Pi-specific. On the MCU side, Adafruit's Protomatter has no
STM32U5 backend; its STM32 support is gated on `#if defined(STM32F4_SERIES)`.

So the pixel pump is offloaded to a XIAO ESP32-S3, which drives HUB75 over
GDMA at almost no CPU cost. **The ESP32 holds no game logic whatsoever** — it
receives finished RGB565 frames and copies them to the panel. It is a display
adapter, exactly as you would use a dedicated driver IC.

```
  ┌──────────────────────────┐        ┌─────────────────┐     ┌──────────┐
  │ UNO Q — STM32            │        │ XIAO ESP32-S3   │HUB75│ 64×32    │
  │ control deck @ 1 kHz     │        │ RGB565 in,      │────►│ panel    │
  │        ↕ router bridge   │  WiFi  │ HUB75 out       │     │          │
  │ UNO Q — Debian / Python  │───────►│ no game logic   │     │          │
  │ games, rendering, Charge │  TCP   └─────────────────┘     └──────────┘
  └──────────────────────────┘  :3333
```

Measured: **114 fps over WiFi**. A frame is 4096 bytes (64×32 in RGB565), so
the link was never the constraint.

---

## The learning games

Six of them, and they do three things an arcade game does not.

*[IMAGE: docs/img/learn.png — the six learning games]*

| Game | Teaches |
|---|---|
| **Gates** | AND / OR / XOR / NAND / NOR |
| **Bit Flip** | binary place value |
| **Pattern** | arithmetic, geometric, Fibonacci, squares |
| **Ohm's Way** | V = I × R, and rearranging it |
| **Gear Lab** | ratios |
| **Angle** | degrees, with the dial as a protractor |

### 1. They explain when you get it wrong

Being told you are wrong teaches nothing. A wrong answer opens a one-line
card saying *why*, then puts you back on the same problem:

*[IMAGE: docs/img/teach.png — explanation cards]*

- `V = I X R` / `3 X 3 = 9`
- `5 IS` / `4+1`
- `ADD 4 EACH` / `SO 19`
- `10 TEETH X 3` / `IS 30`

### 2. Difficulty follows you — per game, not globally

Every game carries **its own level, 1 to 8**, moved by that game's own
evidence. Two first-try corrects in a row promotes; two wrong answers demotes.

This matters more than it sounds. A kid who has binary cold but finds ratios
hard gets **hard binary and gentle ratios at the same time**. A single global
difficulty would hold one back while overwhelming the other.

Only a **first-try** answer counts toward promotion. Arriving at the answer
after three guesses is not the same as knowing it. The bar also rises as you
climb — two in a row early, three from level 4, four from level 6 — so it
takes roughly twenty clean answers to reach level 8.

And the games change *character* near the top, not just their numbers:

| Game | At level 8 |
|---|---|
| Gates | **the gate stops telling you what it is** — flip inputs, watch the output, deduce it |
| Bit Flip | 8 bits, running total **hidden**, sum it yourself |
| Pattern | squares and growing-gap sequences |
| Ohm's Way | awkward numbers, any of the three unknown |
| Gear Lab | real ratios like 5:3, not whole multiples |
| Angle | any angle, no readout, **within 3 degrees by eye** |

### 3. Effort pays

Charge scales with level, and a speed bonus pays up to 10 more for a quick
first-try answer. Pushing your level beats farming easy rounds.

---

## The arcade

*[IMAGE: docs/img/arcade.png — Breakout, Pong, Snake, Simon]*

Breakout is free. Simon costs 40 Charge, Snake 60, Pong 80 — each a one-time
unlock.

Breakout and Pong both use the dial as a paddle, which is the clearest
argument for putting an encoder on a kids' console: the paddle tracks your
wrist instead of ramping to a fixed speed. It plays like the cabinet, not like
a keyboard port.

---

## Hardware

| Part | Notes |
|---|---|
| Arduino UNO Q | Debian image `20251111-426` |
| Seeed XIAO ESP32-S3 | **the u.FL antenna is not optional** — see below |
| Waveshare RGB-Matrix-P3-64x32 | 192 × 96 mm, 1/16 scan, 5 V / 2.5 A |
| EC11 / HW-040 rotary encoder | with push switch |
| 12 mm tactile × 4 | direction cluster |
| 6 mm tactile × 2 | A and B |
| Passive piezo | must be passive — an active buzzer ignores the frequency |
| 5 V / 2.5 A supply | panel only |

### Control deck wiring

All on the UNO Q's own header, read by the STM32.

| Control | Pin |
|---|---|
| Dial — CLK / DT / SW | D2 / D3 / D4 |
| Up / Down / Left / Right | D8 / D9 / D10 / D11 |
| A | D12 |
| B | A5 |
| Buzzer | A0 |

**Feed the HW-040 from 3V3, not 5V.** It carries onboard pull-ups to VCC, so a
5 V supply puts 5 V onto the UNO Q's 3.3 V-logic inputs.

**Do not put a button on D13.** It drives the onboard LED, whose series
resistor to ground fights the internal pull-up and holds the pin below
threshold. A button there reads as permanently pressed. We lost an evening to
this.

### Panel wiring (XIAO → HUB75)

Thirteen signals. The XIAO exposes eleven edge GPIO plus four rear JTAG pads,
so the two least timing-critical lines go on the rear pads.

| HUB75 | XIAO | | HUB75 | XIAO |
|---|---|---|---|---|
| R1 | D0 · GPIO1 | | A | D6 · GPIO43 |
| G1 | D1 · GPIO2 | | B | rear `MTDI` · GPIO41 |
| B1 | D2 · GPIO3 | | C | rear `MTDO` · GPIO40 |
| R2 | D3 · GPIO4 | | D | D7 · GPIO44 |
| G2 | D4 · GPIO5 | | CLK | D8 · GPIO7 |
| B2 | D5 · GPIO6 | | LAT | D9 · GPIO8 |
| GND | GND | | OE | D10 · GPIO9 |

Pin 8 (E) is unused on a 1/16 scan panel. Power the panel from its own 5 V
supply, never from the XIAO's 5V pin, and keep grounds common.

---

## The enclosure

A wedge cabinet — panel leaning back 10°, control deck sloping 18° toward the
player. Three printed parts, no supports, about **150 g of filament**.

*[IMAGE: case/body_view.png — the cabinet]*

Written in OpenSCAD so every dimension is parametric. The screen aperture is
deliberately 4 mm smaller than the panel all round, so the panel seats against
that lip from behind and nothing has to screw through its face — the cabinet
front *is* the bezel.

---

## Four bugs worth writing down

These cost the most time, and every one of them presents as something else.

**The XIAO ESP32-S3 has no PCB antenna.** Without the u.FL antenna clipped on
it saw 4 networks at −85 dBm and could not associate. With it: 16 networks at
−39 dBm. **A 45 dB difference that presents as "wrong WiFi password."**

**USB CDC's receive buffer defaults to 256 bytes.** Against a 4096-byte frame
every full frame arrived truncated — while ping and brightness commands worked
perfectly, because they were small. `Serial.setRxBufferSize(8192)` before
`begin()`.

**The MCU registered its RPCs once, in `setup()`.** The MCU boots in
milliseconds; Linux takes ~40 s to start `arduino-router`. So on any cold boot
the registration silently failed and the controls were dead until someone
reflashed — which would have happened on stage. It now retries from `loop()`
until the router answers.

**A swapped CLK and SW is invisible from software.** The decoder reads a static
pin as CLK against a live DT, producing an endless +1/−1 that never reaches a
whole detent. `enc()` reads exactly zero — identical to a disconnected
encoder. Every test said "no signal" while the signal was there on the wrong
pin.

---

## Build it yourself

Everything is on GitHub: **github.com/lil-shan/pixy**

```bash
# 1. Panel driver — flash the XIAO
cp xiao_wifi/secrets.h.example xiao_wifi/secrets.h   # add your 2.4 GHz SSID
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 \
  --board-options USBMode=hwcdc -u -p /dev/ttyACM0 xiao_wifi

# 2. Control deck — flash the UNO Q's MCU
arduino-cli compile --fqbn arduino:zephyr:unoq -u -p /dev/ttyACM1 mcu/pixy_input

# 3. Console — on the UNO Q
cd ledmatrix && ./pixy.sh start
```

The panel displays its own IP on boot, so you never need a serial monitor to
find it. The ESP32-S3 is **2.4 GHz only** — a 5 GHz-only SSID will never work,
no matter how right the password is.

### A note on Pillow

The Python bridge API and Pillow live inside the App Lab brick container, not
on the host, so `import arduino` fails over SSH. Rather than fight it, Pixy
runs inside that container with the router socket mounted — which means
**no `sudo apt install` is needed at all**:

```bash
docker run --rm --network host \
  -v /var/run/arduino-router.sock:/var/run/arduino-router.sock \
  -v /home/arduino/ledmatrix:/app -w /app \
  --entrypoint python3 ghcr.io/arduino/app-bricks/python-apps-base:0.12.0 \
  -m pixy.app 192.168.1.64
```

---

## What's next

- **Level packs as JSON.** The engines are written; content should be data, so
  a teacher — or a kid — can author levels without touching Python.
- **Camera games** using App Lab's AI bricks, which the UNO Q is built for.
- **Two-player Pong** with a second dial.
- **Sound.** `beep()` is wired throughout and just needs a piezo on A0. Sound
  is most of what separates a hardware toy from a prototype.

---

*Pixy — about 2,500 lines of Python, 440 of Arduino, and 150 of OpenSCAD.*
