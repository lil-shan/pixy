# Build log

Chronological record of what we tried, what broke, and why the design is the
way it is. The README documents the *result*; this documents the *route*.

Each entry is dated and keeps the dead ends in — those are the expensive part.

---

## Hardware as built

### Power rails

The handheld control section uses **common rails**:

- **All grounds are shorted together** — panel supply GND, XIAO GND, UNO Q GND,
  and every button/encoder ground return share one node.
- **Both 3V3 lines are shorted together** — the two HW-040 encoder modules share
  a single 3.3 V rail taken from the UNO Q header.

Two consequences worth remembering:

1. A common ground is *required*, not optional. The HUB75 data lines and the
   button pull-ups are only meaningful relative to a shared reference. Early on,
   driving the panel while its own 5 V rail was absent back-fed it through the
   input ESD clamp diodes — see 2026-09-13 below.
2. The 3.3 V rail is the **only** correct supply for the HW-040 modules. They
   carry onboard pull-ups to VCC, so a 5 V feed would put 5 V onto the UNO Q's
   3.3 V-logic inputs.

### Supply topology

```
5V 2.5A ──────────► Panel VH4
USB charger ──────► XIAO ESP32-S3        (WiFi to UNO Q)
USB-C 5V/3A ──────► UNO Q                (datasheet: PD requests 5V/3A only)
UNO Q 3V3 ────────► both HW-040 modules
        GND ──── common to everything
```

---

## 2026-09-13 — Panel bring-up

**Goal:** get anything at all onto the Waveshare 64×32.

Ruled out driving HUB75 from either half of the UNO Q directly. Linux userspace
has no real-time guarantee, and `rpi-rgb-led-matrix` is Raspberry Pi-specific
(BCM2835 registers). Adafruit_Protomatter has no STM32U5 backend — its STM32
arch is gated on `#if defined(STM32F4_SERIES)`. Offloaded to a XIAO ESP32-S3
driving HUB75 over GDMA.

**Pin budget.** HUB75 needs 13 signals. The XIAO exposes 11 edge GPIO plus four
rear JTAG pads. Put the two least timing-critical lines (address C and D) on the
rear pads, keeping the six colour lines and CLK/LAT/OE on clean edge pins.

### Failures, in order

| Symptom | Cause | Fix |
|---|---|---|
| XIAO never enumerated | Charge-only USB-C cable | Different cable |
| Panel lit with garbage while "unpowered" | Back-fed through input ESD clamp diodes from 13 driven GPIO; rail floated to ~2.5 V and browned out the XIAO | Power the panel first, XIAO second |
| All 32 rows lit but in scrambled order | Address lines B and D crossed | Swapped the pin defines — `xiao_addr` sketch identifies the permutation in one static image |
| Ping and brightness ACKed, frames silently failed | USB CDC RX ring defaults to 256 bytes against a 4096-byte frame | `Serial.setRxBufferSize(8192)` before `begin()` |
| Stream desynchronised permanently | Read both magic bytes in one pass; broke whenever `0xA5` landed at the end of a USB packet | Track the previous byte across loop iterations |
| Serial opened but board unresponsive | pyserial asserts DTR/RTS on open; on the S3's USB Serial/JTAG those drive reset and boot-mode | Clear both *before* opening |

**Result:** 103 fps over USB serial.

---

## 2026-09-13 — Transport moved to WiFi

Wired was chosen first, then reversed. Hosting the XIAO over USB occupies the
UNO Q's only USB-C port, which forces VIN power (7–24 V) and a battery pack to
match. WiFi removes all of it.

Bandwidth was never the constraint: a 64×32 RGB565 frame is 4096 bytes.

**TCP, not UDP** — a frame exceeds the ~1472-byte UDP payload, so UDP would mean
hand-rolling fragmentation and reassembly for no gain at these rates.

### The antenna

The XIAO could see the network but never associated — status 6 (`WL_DISCONNECTED`)
for 30 s, every attempt. Credentials were correct.

| | Networks seen | Target signal |
|---|---|---|
| UNO Q, same desk | 26 | 97 (strong) |
| XIAO, before | 4 | −85 dBm |
| XIAO, after | 16 | **−39 dBm** |

**The XIAO ESP32-S3 has no PCB antenna.** The u.FL antenna was not clipped on.
A 45 dB difference that presents as "wrong WiFi password".

Also: `Tinker Space` is 5 GHz only (ch 36/149). The ESP32-S3 is 2.4 GHz only, so
it could never have joined regardless. Moved everything to a 2.4 GHz SSID.

**Result:** 114 fps over WiFi — faster than USB.

---

## 2026-09-14 — Control deck, Phase 1

**Inputs live on the STM32 side.** Quadrature decoding and debounce need a
jitter-free poll loop; that is what a microcontroller is for and what Linux
userspace is bad at. It also puts both of the UNO Q's brains on the critical
path, which is the board's whole pitch.

### How the two halves talk

Found by inspection rather than documentation:

```
arduino-router --unix-port /var/run/arduino-router.sock \
               --serial-port /dev/ttyHS1 --serial-baudrate 115200
```

STM32 ↔ UART `/dev/ttyHS1` ↔ `arduino-router` ↔ Unix socket ↔ Python.

- **MCU side:** `Arduino_RouterBridge` — `Bridge.provide("name", func)`
- **Python side:** `arduino.app_utils` — `@call()`, `@notify()`, `@provide()`

The Python API ships **inside the App Lab brick container**, not on the host,
which is why `import arduino` fails over SSH.

### Pillow without sudo

`python3-pil` needs root, and the host has no pip, no `ensurepip` and no venv.
Unnecessary: the brick image already carries **PIL 12.3.0, msgpack and arduino**.
Run the code in the container with the router socket mounted:

```bash
docker run --rm --network host \
  -v /var/run/arduino-router.sock:/var/run/arduino-router.sock \
  -v /home/arduino/ledmatrix:/app -w /app \
  --entrypoint python3 ghcr.io/arduino/app-bricks/python-apps-base:0.12.0 script.py
```

### Protocol

One RPC, polled once per frame, packing everything into a single int32 — one
value, no composite msgpack types to get wrong:

```
bits  0-7   buttons held now
bits  8-15  buttons pressed since last poll  (latched, cleared on read)
bits 16-23  encoder 1 delta, signed int8
bits 24-31  encoder 2 delta, signed int8
```

Latching presses on the MCU means a tap between two 30 fps polls is never lost.

### Encoders

Decoded with the 16-entry quadrature table, **not** by counting edges. Cheap
detented encoders bounce, and edge counting turns bounce into phantom counts in
both directions. Illegal transitions map to 0 in the table, so they contribute
nothing. `DETENT_STEPS = 4` because HW-040 emits four transitions per detent.

### Failures

| Symptom | Cause | Fix |
|---|---|---|
| B button read as permanently pressed (`held=0x20`, nothing touched) | D13 drives the onboard LED; its series resistor to ground divides against the ~40 kΩ internal pull-up and holds the pin under threshold | Moved B to **A1**. D13 left unused |

**Result:** bridge RPC round-trips; 7/8 buttons clean before the D13 fix.

---

## Open items

- Encoder direction and detent ratio unverified on hardware
- Buzzer not yet fitted (passive piezo, A0)
- `to_rgb565()` still a pure-Python per-pixel loop — vectorise with numpy
  before the first game, 2048 iterations × 30 fps is on the render path
