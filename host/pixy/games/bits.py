"""Bit Flip -- binary place value.

The lit squares are literally the bits, so the display is the register. Left
and right pick one, A flips it, and the decimal updates as you go.
"""

import random
from ..canvas import (INK, DIM, FAINT, GOOD, CHARGE, LEARN,
                      WIDTH, CONTENT_TOP, CONTENT_BOT)
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

ROUNDS = 5


class Bits(Scene):
    key, title, kind = "bits", "BIT FLIP", "learn"

    def enter(self, ctx):
        self.round, self.score, self.flash = 0, 0, 0
        self.new_round()

    def new_round(self):
        self.width = 4 if self.round < 2 else 8
        self.target = random.randint(1, (1 << self.width) - 1)
        self.value = 0
        self.sel = self.width - 1

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"charge": self.score, "score": self.score})
        if self.flash:
            self.flash -= 1
            if self.flash == 0:
                self.round += 1
                if self.round >= ROUNDS:
                    ctx.profile.mark_solved(self.key, self.round)
                    return ("pop", {"charge": self.score, "score": self.score})
                self.new_round()
            return None

        step = 0
        if s.pressed(RIGHT):
            step -= 1
        if s.pressed(LEFT):
            step += 1
        if s.enc(0):
            step -= s.enc(0)
        if step:
            self.sel = max(0, min(self.width - 1, self.sel + step))

        if s.pressed(A):
            self.value ^= 1 << self.sel
            ctx.deck.beep(800 + self.sel * 90, 15)
            if self.value == self.target:
                self.score += 25
                self.flash = 26
                ctx.deck.beep(1700, 70)
        return None

    def draw(self, c, ctx):
        c.status("BINARY", ctx.profile.charge)

        c.text(1, CONTENT_TOP, "WANT", DIM)
        c.text(22, CONTENT_TOP, str(self.target), CHARGE)
        c.text(40, CONTENT_TOP, "NOW", DIM)
        c.text(53, CONTENT_TOP, str(self.value), INK if self.value else FAINT)

        # Bits, most significant on the left, the way they are written down.
        pitch = 7 if self.width == 8 else 12
        x0 = (WIDTH - self.width * pitch) // 2
        for i in range(self.width):
            bit = self.width - 1 - i
            on = self.value >> bit & 1
            x = x0 + i * pitch
            y = CONTENT_TOP + 8
            c.rect(x, y, 5, 5, GOOD if on else (34, 38, 46))
            if not on:
                c.frame(x, y, 5, 5, FAINT)
            if bit == self.sel:
                c.hline(x, y + 6, 5, LEARN)
                c.hline(x, y - 2, 5, LEARN)

        if self.flash:
            c.banner("+25", GOOD)
        c.hints("A FLIP", f"{self.round + 1}/{ROUNDS}")
