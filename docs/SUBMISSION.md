# Hackster.io submission checklist

Paste `HACKSTER.md` into the Story editor. Everything else below fills in the
sidebar fields.

## Things used in this project

**Hardware components**
- Arduino UNO Q — ×1
- Seeed Studio XIAO ESP32-S3 — ×1
- Waveshare RGB full-colour LED matrix panel, P3, 64×32 — ×1
- Rotary encoder with push button (EC11 / HW-040) — ×1
- Tactile switch, 12 mm — ×4
- Tactile switch, 6 mm — ×2
- Passive piezo buzzer — ×1
- 5 V 2.5 A power supply — ×1
- Jumper wires, perfboard, M3 screws

**Software apps and online services**
- Arduino App Lab
- Arduino IDE / arduino-cli
- Python 3 with Pillow and NumPy
- OpenSCAD

**Hand tools and fabrication machines**
- Soldering iron
- Multimeter
- 3D printer (220 × 220 bed minimum)

## Code
Link the repo: `https://github.com/lil-shan/pixy`
Hackster can import it directly — use "Add code" → GitHub.

## Custom parts and enclosures
Upload from `case/enclosure/`:
- `display_housing.stl` — 199 × 104 × 45 mm, holds panel + XIAO + power bank
- `handheld_controller.stl` — 128 × 88 × 35 mm, holds UNO Q + deck + battery

Optional, from `case/` — an alternative desktop cabinet, designed but not
printed. Only include it if you want to show the direction, and label it as
unbuilt:
- `pixy_case.scad`, `body.stl`, `deck.stl`, `back.stl`

## Images to upload

Real photographs first — they carry the project far better than renders.

| File | Use as |
|---|---|
| `docs/img/screens/console-home.jpeg` | **cover image** |
| `docs/img/architecture.png` | how it works |
| `docs/img/wiring.png` | control deck wiring |
| `docs/img/build/02-xiao-antenna.jpeg` | step 1 |
| `docs/img/build/05-wifi-connecting.jpeg` | step 1 |
| `docs/img/build/03-deck-perfboard.jpeg` | step 2 |
| `docs/img/build/01-unoq-deck-wiring.jpeg` | step 2 |
| `docs/img/build/04-deck-in-shell.jpeg` | step 4 |
| `docs/img/screens/home.jpeg` | step 5 |
| `docs/img/screens/gates.jpeg` | what it is |
| `docs/img/screens/gearlab-close.jpeg` | what it is |
| `docs/img/screens/ohms-way.jpeg` | what it is |
| `docs/img/teach.png` | teach-on-error |

## Videos — upload to YouTube, then embed

| Source file | Where it goes | Why |
|---|---|---|
| `pixyvideo5.mp4` | **top of the story** | Pattern solved, then a LEVEL 2 promotion banner. Shows adaptive difficulty working in 5 seconds |
| `pixyvideo6.mp4` | arcade section | Breakout played on the dial |
| `pixyvideo2.mp4` or `pixyvideo3.mp4` | what it is | someone holding and playing it |

The promotion-banner clip is the single most valuable asset you have. Lead
with it.

## Suggested tags
`arduino-uno-q` `led-matrix` `hub75` `esp32` `education` `stem` `retro-gaming`
`python` `3d-printing`

## One-line summary (Hackster's summary field)
A handheld STEM console where you have to earn the arcade: solve engineering
puzzles on a 64×32 LED matrix to bank Charge, then spend it on Breakout, Pong
and Snake.

Longer pitches for demos and judging are in [PITCH.md](PITCH.md).
