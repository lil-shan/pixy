"""Bit Flip -- binary place value, adaptive."""

import random
from ..canvas import (INK, DIM, FAINT, GOOD, CHARGE, LEARN,
                      WIDTH, CONTENT_TOP)
from ..input import UP, DOWN, LEFT, RIGHT, A
from .learn_base import LearnGame

WIDTH_BY_LEVEL = [3, 4, 5, 6, 7, 8, 8, 8]
HIDE_TOTAL_FROM = 6


class Bits(LearnGame):
    key, title = "bits", "BIT FLIP"
    hint = "A FLIP"

    def setup(self, level):
        lv = min(level, 8)
        self.width = WIDTH_BY_LEVEL[lv - 1]
        # Past level 6 the running total is hidden, so the sum has to be done
        # in your head rather than read off the screen.
        self.hide_total = lv >= HIDE_TOTAL_FROM
        self.target = random.randint(1, (1 << self.width) - 1)
        self.value = 0
        # Start from a random position rather than always the far end, so the
        # first few moves are not the same every round.
        self.sel = random.randrange(self.width)

    def header(self):
        return "BINARY"

    def explain(self):
        # Show the place values that actually make up the target. This is the
        # whole lesson: a number is a sum of powers of two.
        parts = [str(1 << b) for b in range(self.width - 1, -1, -1)
                 if self.target >> b & 1]
        return ("%d IS" % self.target, "+".join(parts))

    def play(self, s, ctx):
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
            ctx.deck.beep(800 + self.sel * 90, 12)
            if self.value == self.target:
                self.submit(ctx, True)
            elif self.value > self.target:
                # Overshooting is the teachable moment, so say so rather than
                # letting them flail.
                self.submit(ctx, False)
        return None

    def draw_problem(self, c, ctx):
        c.text(1, CONTENT_TOP, "WANT", DIM)
        c.text(22, CONTENT_TOP, str(self.target), CHARGE)
        if not self.hide_total:
            c.text(40, CONTENT_TOP, "NOW", DIM)
            c.text(53, CONTENT_TOP, str(self.value), INK if self.value else FAINT)
        else:
            c.text(44, CONTENT_TOP, "? ?", FAINT)
        pitch = 7 if self.width > 4 else 12
        x0 = (WIDTH - self.width * pitch) // 2
        for i in range(self.width):
            bit = self.width - 1 - i
            on = self.value >> bit & 1
            x, y = x0 + i * pitch, CONTENT_TOP + 8
            c.rect(x, y, 5, 5, GOOD if on else (34, 38, 46))
            if not on:
                c.frame(x, y, 5, 5, FAINT)
            if bit == self.sel:
                c.hline(x, y + 6, 5, LEARN)
                c.hline(x, y - 2, 5, LEARN)
