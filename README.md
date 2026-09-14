# UNO Q LED Matrix

Driving a Waveshare 64×32 HUB75 RGB LED matrix from an Arduino UNO Q, with a
XIAO ESP32-S3 acting as the panel's display adapter.

All rendering — fonts, images, GIFs, scrolling, effects — runs in Python on the
UNO Q's Linux side. The ESP32 holds no application logic at all: it receives
finished RGB565 frames and copies them to the panel.

## Why there's a second microcontroller

A HUB75 panel has no framebuffer and no PWM of its own. Something must
continuously bit-bang thirteen signals at ~100+ full refreshes per second, with
binary code modulation layered on top for colour depth. That needs either DMA
hardware or a dedicated real-time core.

Neither half of the UNO Q can do it well. Linux userspace has no real-time
guarantee, so GPIO bit-banging flickers; and the standard Linux HUB75 library
(`rpi-rgb-led-matrix`) pokes BCM2835 registers directly and is Raspberry
Pi-specific. The STM32U585 is fast enough in principle, but Adafruit_Protomatter
has no U5 support — its STM32 backend is gated on `STM32F4_SERIES`.

So the pixel pump is offloaded to an ESP32-S3, which drives HUB75 over GDMA with
almost no CPU cost. It's the same reasoning you'd use to pick a dedicated
display driver IC. The interesting work stays on the UNO Q.

## Architecture

```
  ┌─────────────────────────┐         ┌──────────────────┐      ┌─────────┐
  │ UNO Q (Debian, Python)  │  WiFi   │ XIAO ESP32-S3    │HUB75 │ 64×32   │
  │ Pillow: text, images,   │────────►│ receives RGB565, │─────►│ panel   │
  │ GIFs, scrolling         │  TCP    │ blits via GDMA   │      │         │
  └─────────────────────────┘  :3333  └──────────────────┘      └─────────┘
                                                                     ▲
                                                     5V 2.5A supply ─┘
```

Measured throughput: **114 fps** over WiFi, **103 fps** over USB serial. A frame
is 4096 bytes (64×32 × RGB565), so the link was never the constraint.

## Hardware

| Part | Notes |
|---|---|
| Arduino UNO Q | Debian image `BUILD_ID=20251111-426` |
| Seeed XIAO ESP32-S3 | **External antenna required** — no PCB antenna |
| Waveshare RGB-Matrix-P3-64x32 | 1/16 scan, HUB75E connector |
| 5 V / 2.5 A supply | Panel only, via the VH4 socket |

## Wiring

HUB75 needs 13 signals. The XIAO exposes 11 edge GPIO plus four rear JTAG pads,
so two rear pads carry the two least timing-critical lines.

| HUB75 pin | Signal | XIAO | GPIO |
|---|---|---|---|
| 1 | R1 | D0 | 1 |
| 2 | G1 | D1 | 2 |
| 3 | B1 | D2 | 3 |
| 4 | GND | GND | — |
| 5 | R2 | D3 | 4 |
| 6 | G2 | D4 | 5 |
| 7 | B2 | D5 | 6 |
| 8 | E | *unconnected* | — |
| 9 | A | D6 | 43 |
| 10 | B | rear pad MTDI | 41 |
| 11 | C | rear pad MTDO | 40 |
| 12 | D | D7 | 44 |
| 13 | CLK | D8 | 7 |
| 14 | LAT | D9 | 8 |
| 15 | OE | D10 | 9 |
| 16 | GND | GND | — |

Pin 8 is the E address line, unused on a 1/16 scan panel. Power the panel from
its own 5 V supply — never from the XIAO's 5V pin — and keep grounds common.

## Control deck

| Control | Pin | Notes |
|---|---|---|
| Dial — CLK / DT / SW | D2 / D3 / D4 | HW-040 module |
| Up / Down / Left / Right | D8 / D9 / D10 / D11 | Big tactile, internal pull-ups |
| A / B | D12 / A1 | Small tactile |
| Buzzer | A0 | Passive piezo — an active one ignores the frequency |

One dial only. A second encoder was tried and abandoned; `enc(1)` is still
wired through and returns 0, so one can be added later without touching any
game.

## Controls

The grammar never varies, on any screen:

| Control | Always does |
|---|---|
| Dial | Move through choices, set a value |
| A | Confirm, act |
| B | Back, cancel |
| D-pad | Direction, inside games |

Every screen carries a hint bar saying what A and B do right now, every game
opens with a two-line help card, and a first-run tutorial makes you use each
control once before it lets you into the menus.

**Common rails.** All grounds are shorted together across the panel supply, the
XIAO, the UNO Q and every button return. Both HW-040 modules share one 3.3 V rail
from the UNO Q header.

**Feed the HW-040s from 3V3, not 5V.** They carry onboard pull-ups to VCC, so a
5 V supply puts 5 V onto the UNO Q's 3.3 V-logic inputs. Their onboard pull-ups
also mean you don't need external ones on CLK/DT.

**D13 is unusable as a button input.** It drives the onboard LED, whose series
resistor to ground divides against the ~40 kΩ internal pull-up and holds the pin
below threshold — a button there reads as permanently pressed. That's why B is
on A1.

See [BUILDLOG.md](BUILDLOG.md) for the full iteration history — every failure,
its cause and its fix.

## Setup

**ESP32 side**

```bash
cp xiao_wifi/secrets.h.example xiao_wifi/secrets.h   # then fill in your SSID/password
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 \
  --board-options USBMode=hwcdc -u -p /dev/ttyACM0 xiao_wifi
```

The panel displays its own IP address on boot, so no serial monitor is needed to
find it.

**UNO Q side**

```bash
sudo apt install -y python3-pil
python3 -c "
from panel import Panel
p = Panel(host='192.168.1.64')
p.text('HELLO')
"
```

## Learning games

Six, each with its own adaptive level:

| Game | Teaches |
|---|---|
| Gate Keeper | AND / OR / XOR / NAND / NOR |
| Bit Flip | binary place value |
| Pattern | arithmetic, geometric and Fibonacci sequences |
| Ohm's Way | V = I x R, and rearranging it |
| Gear Lab | ratios |
| Angle | degrees, with the dial as a protractor |

**They adapt independently, across eight levels.** Two first-try corrects in a
row moves that game up; two wrong answers moves it down. The bar to climb
rises with the level -- two in a row early, three from level 4, four from
level 6 -- so the top is earned rather than stumbled into. Roughly twenty
clean answers to reach level 8.

What changes as you climb:

| Game | At the top |
|---|---|
| Gates | the gate stops telling you what it is; deduce it by experiment |
| Bit Flip | 8 bits, and the running total is hidden -- sum it yourself |
| Pattern | squares and growing-gap sequences, not just constant steps |
| Ohm's Way | awkward numbers, any of the three unknown |
| Gear Lab | real ratios like 5:3, not whole multiples |
| Angle | any angle, no readout, within 3 degrees by eye |

Two first-try corrects in a row moves that game up a level; two wrong moves it
down. A kid who has binary cold but
finds ratios hard gets hard binary and gentle ratios at the same time, which a
single global difficulty could never do. Charge paid scales with level, so
pushing yourself beats farming easy rounds.

**They explain.** A wrong answer opens a one-line card saying *why* -- "V = I
X R / 3 X 3 = 9", "5 IS / 4+1", "ADD 4 EACH / SO 19" -- then puts you back on
the same problem. Being told you are wrong teaches nothing on its own.

## API

```python
from panel import Panel

p = Panel(host='192.168.1.64')   # WiFi
p = Panel()                      # or USB serial, autodetected

p.text('HELLO')                            # centred, auto-shrinks to fit
p.scroll('longer message', speed=0.02)     # any length, any font
p.image('logo.png')                        # scaled, aspect preserved
p.gif('animation.gif')                     # honours per-frame timing
p.brightness(60)
p.clear()
p.ping()                                   # round-trip check
```

## Protocol

```
0xA5 0x5A <cmd> <len:uint16 LE> <payload...>
  0x01  frame       4096 bytes RGB565, big endian per pixel
  0x02  brightness  1 byte
  0x03  clear       no payload
  0x04  ping        no payload
```

Each handled command is acknowledged with a single `0x06` byte, so the host can
verify delivery rather than relying on someone watching the panel.

## Sketches

| Sketch | Purpose |
|---|---|
| `xiao_wifi` | **Main.** WiFi receiver, TCP server on :3333 |
| `xiao_receiver` | Same receiver over USB serial |
| `xiao_panel` | Standalone demo — colour bars, scrolling text, bitmap |
| `xiao_diag` | Slow static diagnostic: flat fills, half-split, row sweep |
| `xiao_addr` | Identifies which address line is wired where |

## Things that bit us

Kept because every one cost real debugging time.

- **The XIAO ESP32-S3 has no PCB antenna.** Without the u.FL antenna attached it
  saw 4 networks at −85 dBm and could not associate. With it: 16 networks,
  −39 dBm. A 45 dB difference that presents as "wrong WiFi password".
- **`Tinker Space` was 5 GHz only.** The ESP32-S3 is 2.4 GHz only, so it could
  never have joined regardless of credentials.
- **Address lines B and D were crossed.** Every row lit, but in scrambled order —
  a pure permutation. Fixed in software by swapping the pin defines; `xiao_addr`
  identifies the mapping in one static image.
- **USB CDC RX buffer defaults to 256 bytes.** Against a 4096-byte frame, every
  full frame arrived truncated while ping and brightness worked perfectly.
  `Serial.setRxBufferSize(8192)` before `begin()`.
- **Reading the two magic bytes in one pass desynchronises the stream** whenever
  `0xA5` lands at the end of a USB packet. Track the previous byte across loop
  iterations instead.
- **pyserial asserts DTR and RTS on open**, which on the S3's USB Serial/JTAG
  peripheral drives reset and boot-mode selection. Clear both *before* opening.
- **Driving an unpowered panel back-feeds it** through the input ESD clamp
  diodes, lighting it dimly with garbage and browning out the XIAO. Power the
  panel first, then the XIAO.
