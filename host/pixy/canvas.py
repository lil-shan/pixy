"""Drawing surface for a 64x32 panel.

Carries a hand-built 3x5 pixel font. PIL's bundled font is ~11 px tall, which
eats a third of the screen per line and anti-aliases into mush at this size.
A bitmap font drawn on exact pixel boundaries stays crisp, which is the whole
reason retro consoles look sharp and scaled-down desktop UI does not.
"""

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 64, 32

# Screen furniture. 32 rows split 6 / 20 / 6 -- status, content, hints.
STATUS_H, HINT_Y = 6, 26
CONTENT_TOP, CONTENT_BOT = 7, 25

# Palette. Saturated and few, because RGB565 on 3 mm pitch rewards contrast
# over subtlety, and kids read colour faster than shape at this resolution.
INK      = (235, 238, 245)
DIM      = (88, 98, 112)
FAINT    = (40, 46, 56)
CHARGE   = (255, 192, 46)
LEARN    = (79, 209, 197)
ARCADE   = (255, 97, 130)
GOOD     = (95, 224, 140)
BAD      = (242, 85, 90)
BG       = (0, 0, 0)

# 3x5 glyphs, one int per row, bit 2 = leftmost pixel.
_F = {
    "A": (0b010, 0b101, 0b111, 0b101, 0b101), "B": (0b110, 0b101, 0b110, 0b101, 0b110),
    "C": (0b011, 0b100, 0b100, 0b100, 0b011), "D": (0b110, 0b101, 0b101, 0b101, 0b110),
    "E": (0b111, 0b100, 0b110, 0b100, 0b111), "F": (0b111, 0b100, 0b110, 0b100, 0b100),
    "G": (0b011, 0b100, 0b101, 0b101, 0b011), "H": (0b101, 0b101, 0b111, 0b101, 0b101),
    "I": (0b111, 0b010, 0b010, 0b010, 0b111), "J": (0b001, 0b001, 0b001, 0b101, 0b010),
    "K": (0b101, 0b101, 0b110, 0b101, 0b101), "L": (0b100, 0b100, 0b100, 0b100, 0b111),
    "M": (0b101, 0b111, 0b111, 0b101, 0b101), "N": (0b101, 0b111, 0b111, 0b111, 0b101),
    "O": (0b010, 0b101, 0b101, 0b101, 0b010), "P": (0b110, 0b101, 0b110, 0b100, 0b100),
    "Q": (0b010, 0b101, 0b101, 0b111, 0b011), "R": (0b110, 0b101, 0b110, 0b101, 0b101),
    "S": (0b011, 0b100, 0b010, 0b001, 0b110), "T": (0b111, 0b010, 0b010, 0b010, 0b010),
    "U": (0b101, 0b101, 0b101, 0b101, 0b111), "V": (0b101, 0b101, 0b101, 0b101, 0b010),
    "W": (0b101, 0b101, 0b111, 0b111, 0b101), "X": (0b101, 0b101, 0b010, 0b101, 0b101),
    "Y": (0b101, 0b101, 0b010, 0b010, 0b010), "Z": (0b111, 0b001, 0b010, 0b100, 0b111),
    "0": (0b111, 0b101, 0b101, 0b101, 0b111), "1": (0b010, 0b110, 0b010, 0b010, 0b111),
    "2": (0b110, 0b001, 0b010, 0b100, 0b111), "3": (0b110, 0b001, 0b010, 0b001, 0b110),
    "4": (0b101, 0b101, 0b111, 0b001, 0b001), "5": (0b111, 0b100, 0b110, 0b001, 0b110),
    "6": (0b011, 0b100, 0b111, 0b101, 0b111), "7": (0b111, 0b001, 0b010, 0b010, 0b010),
    "8": (0b111, 0b101, 0b111, 0b101, 0b111), "9": (0b111, 0b101, 0b111, 0b001, 0b110),
    " ": (0, 0, 0, 0, 0),                      "-": (0, 0, 0b111, 0, 0),
    ":": (0, 0b010, 0, 0b010, 0),              "!": (0b010, 0b010, 0b010, 0, 0b010),
    "?": (0b110, 0b001, 0b010, 0, 0b010),      ".": (0, 0, 0, 0, 0b010),
    "/": (0b001, 0b001, 0b010, 0b100, 0b100),  "+": (0, 0b010, 0b111, 0b010, 0),
    "=": (0, 0b111, 0, 0b111, 0),              "<": (0b001, 0b010, 0b100, 0b010, 0b001),
    ">": (0b100, 0b010, 0b001, 0b010, 0b100),  "*": (0b101, 0b010, 0b101, 0, 0),
    "%": (0b101, 0b001, 0b010, 0b100, 0b101),  "'": (0b010, 0b010, 0, 0, 0),
}


def text_width(s):
    return max(0, len(s) * 4 - 1)


class Canvas:
    """One frame, with helpers that know the screen's furniture."""

    def __init__(self):
        self.img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        self.d = ImageDraw.Draw(self.img)

    # ── primitives ────────────────────────────────────────────────────────
    def px(self, x, y, c):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.img.putpixel((int(x), int(y)), c)

    def rect(self, x, y, w, h, c):
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

    def frame(self, x, y, w, h, c):
        self.d.rectangle([x, y, x + w - 1, y + h - 1], outline=c)

    def hline(self, x, y, w, c):
        self.d.line([(x, y), (x + w - 1, y)], fill=c)

    def text(self, x, y, s, c=INK):
        """Draw uppercase 3x5 text. Unknown characters are skipped."""
        for ch in str(s).upper():
            g = _F.get(ch)
            if g:
                for row in range(5):
                    bits = g[row]
                    for col in range(3):
                        if bits & (1 << (2 - col)):
                            self.px(x + col, y + row, c)
            x += 4

    def text_centre(self, y, s, c=INK):
        self.text((WIDTH - text_width(s)) // 2, y, s, c)

    # ── furniture ─────────────────────────────────────────────────────────
    def status(self, title, charge=None):
        """Top bar: where you are on the left, Charge battery on the right."""
        self.text(1, 0, title[:12], DIM)
        if charge is not None:
            x = WIDTH - 13
            self.frame(x, 0, 10, 5, CHARGE)
            self.px(x + 10, 2, CHARGE)
            fill = max(0, min(8, int(charge / 500 * 8)))
            if fill:
                self.rect(x + 1, 1, fill, 3, CHARGE)
        self.hline(0, STATUS_H - 1, WIDTH, FAINT)

    def hints(self, left=None, right=None):
        """Bottom bar: what the two buttons do right now."""
        self.hline(0, HINT_Y, WIDTH, FAINT)
        if left:
            self.text(1, HINT_Y + 1, left, DIM)
        if right:
            self.text(WIDTH - 1 - text_width(right), HINT_Y + 1, right, DIM)

    def banner(self, line, c=INK, sub=None):
        self.rect(4, 11, WIDTH - 8, 11, BG)
        self.frame(4, 11, WIDTH - 8, 11, c)
        self.text_centre(13, line, c)
        if sub:
            self.text_centre(19, sub, DIM)
