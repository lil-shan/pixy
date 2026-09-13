"""Render Pixy screens to a contact sheet, as the panel would show them.

No hardware needed. Scales each 64x32 frame up and lays an LED pitch mask over
it, so what you see on screen matches what the panel actually looks like --
which is the only way to judge legibility at this resolution.

    python3 tools/shots.py out.png
"""

import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "host"))

_stub = types.ModuleType("panel")
class _P:
    def __init__(self, *a, **k): pass
    def brightness(self, *a): pass
    def show(self, *a, **k): return True
    def clear(self): pass
_stub.Panel = _P; _stub.WIDTH = 64; _stub.HEIGHT = 32
sys.modules["panel"] = _stub

from PIL import Image, ImageDraw                      # noqa: E402
from pixy.canvas import Canvas                        # noqa: E402
from pixy.input import State                          # noqa: E402
from pixy.profile import Profile                      # noqa: E402

SCALE = 7
GAP = 14
LABEL_H = 16


def led_ify(img):
    """Upscale and punch out the gaps between LEDs."""
    big = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
    mask = Image.new("RGB", big.size, (0, 0, 0))
    d = ImageDraw.Draw(mask)
    r = SCALE * 0.36
    for y in range(img.height):
        for x in range(img.width):
            cx, cy = x * SCALE + SCALE / 2, y * SCALE + SCALE / 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=img.getpixel((x, y)))
    return mask


def shoot(scene, ctx, frames=1, feed=None):
    """Run a scene for N frames and return the last rendered canvas."""
    scene.enter(ctx)
    c = None
    for i in range(frames):
        s = feed(i) if feed else State(0)
        scene.update(s, ctx)
        c = Canvas()
        scene.draw(c, ctx)
    return c.img


def sheet(shots, path, cols=3):
    rows = (len(shots) + cols - 1) // cols
    tw = 64 * SCALE
    th = 32 * SCALE + LABEL_H
    out = Image.new("RGB", (cols * tw + (cols + 1) * GAP,
                            rows * th + (rows + 1) * GAP), (24, 26, 30))
    d = ImageDraw.Draw(out)
    for i, (name, img) in enumerate(shots):
        r, c = divmod(i, cols)
        x = GAP + c * (tw + GAP)
        y = GAP + r * (th + GAP)
        out.paste(led_ify(img), (x, y + LABEL_H))
        d.text((x + 2, y + 3), name, fill=(200, 205, 215))
    out.save(path)
    return out.size
