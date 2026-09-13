"""Phase 1 acceptance test: every control, live on the panel.

Run this after wiring the deck. It proves the whole chain in one shot --
STM32 scan, router bridge, Python unpack, frame render, HUB75 output. If a
button lights its dot and an encoder moves its bar, Phase 1 is done.

    python3 -m pixy.decktest 192.168.1.64
"""

import os
import sys
import time

from PIL import Image, ImageDraw

# panel.py sits next to the pixy package, wherever that has been deployed.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from panel import Panel, WIDTH, HEIGHT          # noqa: E402
from pixy.input import Deck, NAMES, UP, DOWN, LEFT, RIGHT, A, B, START, SELECT  # noqa: E402

# Where each control draws itself. The four directions sit in a cluster that
# mirrors the physical deck, so a miswired button is obvious at a glance
# rather than needing to be reasoned about.
# SELECT is omitted: it was the second encoder's push, and that encoder is
# no longer fitted.
LAYOUT = {
    UP:     (10, 9), DOWN: (10, 19), LEFT: (4, 14), RIGHT: (16, 14),
    A:      (32, 11), B: (32, 19),
    START:  (44, 15),
}
COLOUR = {
    UP: (80, 220, 255), DOWN: (80, 220, 255), LEFT: (80, 220, 255), RIGHT: (80, 220, 255),
    A: (95, 224, 140), B: (242, 85, 90),
    START: (255, 192, 46),
}


def main(host, seconds=None):
    panel = Panel(host=host)
    panel.brightness(70)
    deck = Deck()
    print("polling -- press things. ctrl-c to stop.")

    enc = [0, 0]
    seen = set()
    last_report = 0.0
    deadline = time.time() + seconds if seconds else None

    try:
        while deadline is None or time.time() < deadline:
            s = deck.poll()
            enc[0] = max(-16, min(16, enc[0] + s.enc(0)))
            enc[1] = max(-16, min(16, enc[1] + s.enc(1)))

            img = Image.new("RGB", (WIDTH, HEIGHT))
            d = ImageDraw.Draw(img)

            # A filled 3x3 block when held, a single dim pixel when not, so the
            # resting state still shows you the control exists.
            for btn, (x, y) in LAYOUT.items():
                if s.down(btn):
                    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=COLOUR[btn])
                else:
                    d.point((x, y), fill=(40, 46, 56))

            # One dial, one bar. Turning clockwise must move it consistently
            # one way -- that is the sign convention, and it is worth checking
            # before games are written against it.
            d.line([(56, 4), (56, 28)], fill=(40, 46, 56))
            cursor = 16 - int(enc[0] / 16 * 11)
            d.rectangle([53, cursor - 1, 59, cursor + 1], fill=(79, 209, 197))

            panel.show(img)

            for btn in LAYOUT:
                if s.pressed(btn) and btn not in seen:
                    seen.add(btn)
                    print(f"  first press: {NAMES[btn]}   ({len(seen)}/8 controls seen)")
                    deck.beep(660 + 60 * btn, 30)

            now = time.time()
            if (s.enc(0) or s.enc(1)) and now - last_report > 0.3:
                last_report = now
                print(f"  encoders: {enc[0]:+3d} {enc[1]:+3d}")

            time.sleep(1 / 30)
    except KeyboardInterrupt:
        print(f"\nsaw {len(seen)}/{len(LAYOUT)} controls: {sorted(NAMES[b] for b in seen)}")
        missing = [NAMES[b] for b in LAYOUT if b not in seen]
        if missing:
            print(f"never pressed: {', '.join(missing)}")
        panel.clear()
        if hasattr(deck, "close"):
            deck.close()


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.64"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else None
    main(host, secs)
