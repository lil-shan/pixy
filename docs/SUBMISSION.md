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
Upload from `case/`:
- `body.stl` — cabinet
- `deck.stl` — control plate
- `back.stl` — rear cover
- `pixy_case.scad` — parametric source

## Images to upload
| File | Use as |
|---|---|
| `docs/img/shell.png` | cover image |
| `docs/img/learn.png` | the six learning games |
| `docs/img/teach.png` | explanation cards |
| `docs/img/arcade.png` | arcade games |
| `docs/img/case.png` | enclosure render |

**Take these before submitting** — they matter more than any render:
1. The finished console, powered on, showing a learning game
2. A close-up of the control deck
3. Someone actually playing it

## Suggested tags
`arduino-uno-q` `led-matrix` `hub75` `esp32` `education` `stem` `retro-gaming`
`python` `3d-printing`

## One-line summary
A STEM learning console for kids: solve engineering puzzles on a 64×32 LED
matrix, earn Charge, spend it in the arcade. Uses both of the UNO Q's brains.
