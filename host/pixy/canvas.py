"""Drawing surface for a 64x32 panel.

Carries a hand-built 3x5 pixel font. PIL's bundled font is ~11 px tall, which
eats a third of the screen per line and anti-aliases into mush at this size.
A bitmap font drawn on exact pixel boundaries stays crisp, which is the whole
reason retro consoles look sharp and scaled-down desktop UI does not.
"""

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 64, 32

# Screen furniture, in rows. The glyphs are 5 tall, so every band is sized in
# multiples of 6 and the content band holds exactly three rows. Getting this
# wrong clips the last line, which is invisible until you look at real output.
#
#   0-4    status text      5  separator
#   7-23   content          three 6px rows at 7, 13, 19
#   25     separator        26-30  hint text
STATUS_H     = 6
CONTENT_TOP  = 7
CONTENT_BOT  = 23
ROW_H        = 6
ROWS         = 3
HINT_SEP     = 25
HINT_Y       = 26

# Palette. Saturated and few, because RGB565 on 3 mm pitch rewards contrast
# over subtlety, and kids read colour faster than shape at this resolution.
# Values are deliberately high. On a 3 mm-pitch panel at working brightness
# anything under ~120 reads as off, so "subtle" greys simply vanish.
INK      = (245, 247, 252)
DIM      = (158, 168, 184)
FAINT    = (72, 80, 94)
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
        """Top bar: where you are on the left, Charge battery on the right.

        The title is clipped to what actually fits beside the battery, rather
        than a guessed character count -- otherwise long titles run under it.
        """
        limit = (WIDTH - 15) // 4 if charge is not None else WIDTH // 4
        self.text(1, 0, str(title)[:limit], INK)
        if charge is not None:
            x = WIDTH - 13
            self.frame(x, 0, 10, 5, CHARGE)
            self.px(x + 10, 2, CHARGE)
            fill = max(0, min(8, int(charge / 500 * 8)))
            if fill:
                self.rect(x + 1, 1, fill, 3, CHARGE)
        self.hline(0, STATUS_H - 1, WIDTH, FAINT)

    def hints(self, left=None, right=None):
        """Bottom bar: what the buttons do right now. Never leave it empty --
        not knowing which button to press is the single worst failure on a
        device with no labels."""
        self.hline(0, HINT_SEP, WIDTH, FAINT)
        if left:
            self.text(1, HINT_Y, str(left), DIM)
        if right:
            self.text(WIDTH - 1 - text_width(str(right)), HINT_Y, str(right), DIM)

    # Width reserved on the right for scroll arrows, so row text and notes
    # can be inset instead of being drawn under them.
    SCROLL_W = 4

    def scroll_marks(self, top, shown, total):
        """Arrows showing there is more above or below. Without them a list
        that scrolls just looks like a list that is missing items."""
        x = WIDTH - 3
        if top > 0:
            for i in range(2):
                self.px(x - i, CONTENT_TOP + 1 + i, DIM)
                self.px(x + i, CONTENT_TOP + 1 + i, DIM)
        if top + shown < total:
            for i in range(2):
                self.px(x - i, CONTENT_BOT - 1 - i, DIM)
                self.px(x + i, CONTENT_BOT - 1 - i, DIM)

    def card(self, lines, accent=INK):
        """Help card body. The title already sits in the status bar, so
        repeating it here just wastes two of the seventeen usable rows."""
        self.rect(0, CONTENT_TOP, WIDTH, CONTENT_BOT - CONTENT_TOP + 1, BG)
        for i, line in enumerate(lines[:2]):
            col = accent if i == 0 else DIM
            self.text_centre(CONTENT_TOP + 2 + i * 7, str(line)[:15], col)

    def banner(self, line, c=INK, sub=None):
        """Modal message. Sized to sit inside the content band so it never
        collides with the status or hint bars."""
        h = 17 if sub else 11
        y = CONTENT_TOP + (CONTENT_BOT - CONTENT_TOP + 1 - h) // 2
        self.rect(3, y, WIDTH - 6, h, BG)
        self.frame(3, y, WIDTH - 6, h, c)
        self.text_centre(y + 3, line, c)
        if sub:
            self.text_centre(y + 10, sub, DIM)
