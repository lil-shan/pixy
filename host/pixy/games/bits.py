"""Bit Flip -- binary place value.

Eight LEDs are literally eight bits, so the display *is* the register. Left and
right pick a bit, A flips it, and the running decimal updates as you go.
"""

import random
from ..canvas import INK, DIM, GOOD, CHARGE, LEARN
from ..scene import Scene


class Bits(Scene):
    key, title, kind = "bits", "BIT FLIP", "learn"

    def enter(self, ctx):
        self.round, self.score = 0, 0
        self.new_round()
        self.flash = 0

    def new_round(self):
        hi = 15 if self.round < 2 else 255
        self.target = random.randint(1, hi)
        self.value = 0
        self.sel = 7 if hi > 15 else 3
        self.width = 8 if hi > 15 else 4

    def update(self, s, ctx):
        if s.pressed(6):
            return ("pop", {"charge": self.score, "score": self.score})
        if self.flash:
            self.flash -= 1
            if self.flash == 0:
                self.round += 1
                if self.round >= 5:
                    return ("pop", {"charge": self.score, "score": self.score})
                self.new_round()
            return None

        if s.pressed(2):
            self.sel = min(self.width - 1, self.sel + 1)
        if s.pressed(3):
            self.sel = max(0, self.sel - 1)
        if s.enc(0):
            self.sel = max(0, min(self.width - 1, self.sel - s.enc(0)))
        if s.pressed(4):
            self.value ^= 1 << self.sel
            if self.value == self.target:
                self.score += 25
                self.flash = 24
        return None

    def draw(self, c, ctx):
        c.status("BINARY", ctx.profile.charge)
        c.text(2, 8, "WANT", DIM)
        c.text(24, 8, str(self.target), CHARGE)

        # Bits drawn most-significant first, matching how they are written.
        x0 = 32 - (self.width * 7) // 2
        for i in range(self.width):
            bit = self.width - 1 - i
            on = self.value >> bit & 1
            x = x0 + i * 7
            c.rect(x, 15, 5, 5, GOOD if on else (30, 34, 42))
            if bit == self.sel:
                c.hline(x, 21, 5, LEARN)

        c.text(2, 15, "=", DIM)
        c.text(2, 21, str(self.value), INK)
        if self.flash:
            c.banner("MATCH +25", GOOD)
        c.hints("A FLIP", f"{self.round + 1}/5")
