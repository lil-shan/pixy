"""Gear Lab -- ratios.

Dial the driven gear until the ratio matches. Both wheels turn, and the driven
one turns slower by exactly the ratio, so the lesson is visible before it is
stated.
"""

import random
from math import gcd, cos, sin, pi
from ..canvas import INK, DIM, FAINT, GOOD, CHARGE, LEARN, CONTENT_TOP, CONTENT_BOT
from .learn_base import DialGame


class Gears(DialGame):
    key, title = "gears", "GEAR LAB"
    lo, hi = 4, 60
    hint = "A LOCK"

    def setup(self, level):
        self.driver = random.choice([8, 10, 12] if level <= 2 else [6, 8, 9, 10, 12])
        mult = random.choice([2, 3] if level <= 2 else
                             [2, 3, 4] if level <= 4 else [2, 3, 4, 5])
        self.answer = self.driver * mult
        self.mult = mult
        self.value = self.driver
        self.phase = 0.0

    def explain(self):
        return ("%d TEETH X %d" % (self.driver, self.mult),
                "IS %d" % self.answer)

    def ratio_text(self, a, b):
        g = gcd(a, b)
        return "%d:%d" % (a // g, b // g)

    def play(self, s, ctx):
        self.phase += 3.0
        return super().play(s, ctx)

    def wheel(self, c, cx, cy, r, teeth, col, phase):
        dim = tuple(v // 3 for v in col)
        for deg in range(0, 360, 8):
            a = deg * pi / 180
            c.px(round(cx + cos(a) * r), round(cy + sin(a) * r), dim)
        n = max(5, min(12, teeth))
        for i in range(n):
            a = (phase + i * 360.0 / n) * pi / 180
            c.px(round(cx + cos(a) * (r + 1)), round(cy + sin(a) * (r + 1)), col)
        c.px(cx, cy, col)

    def draw_problem(self, c, ctx):
        mid = CONTENT_TOP + 4
        self.wheel(c, 9, mid, 4, self.driver, LEARN, self.phase)
        self.wheel(c, 25, mid, 5, self.value, CHARGE,
                   -self.phase * self.driver / max(1, self.value))
        c.text(5, CONTENT_BOT - 4, str(self.driver), LEARN)
        c.text(22, CONTENT_BOT - 4, str(self.value), CHARGE)
        c.text(40, CONTENT_TOP, "WANT", DIM)
        c.text(40, CONTENT_TOP + 7, "1:%d" % self.mult, INK)
        ok = self.value == self.answer
        c.text(40, CONTENT_TOP + 14, "OK" if ok else "..", GOOD if ok else FAINT)
