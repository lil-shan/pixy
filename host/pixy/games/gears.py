"""Gear Lab -- ratios.

Dial the driven gear until the ratio matches the target. The encoder is the
right control here because a ratio is a continuous quantity: you feel it
approach rather than typing a number.
"""

import random
from math import gcd
from ..canvas import INK, DIM, GOOD, CHARGE, LEARN
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B


class Gears(Scene):
    key, title, kind = "gears", "GEAR LAB", "learn"

    def enter(self, ctx):
        self.round, self.score = 0, 0
        self.new_round()
        self.flash = 0

    def new_round(self):
        self.driver = random.choice([8, 10, 12, 15, 20])
        mult = random.choice([2, 3, 4]) if self.round < 2 else random.choice([2, 3, 4, 5])
        self.want = self.driver * mult
        self.driven = 8
        self.phase = 0.0

    def _ratio(self, a, b):
        g = gcd(a, b)
        return f"{a // g}:{b // g}"

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"charge": self.score, "score": self.score})
        self.phase += 0.25
        if self.flash:
            self.flash -= 1
            if self.flash == 0:
                self.round += 1
                if self.round >= 5:
                    return ("pop", {"charge": self.score, "score": self.score})
                self.new_round()
            return None

        step = s.enc(0)
        if s.pressed(RIGHT):
            step += 1
        if s.pressed(LEFT):
            step -= 1
        if step:
            self.driven = max(4, min(120, self.driven + step))
        if s.pressed(A) and self.driven == self.want:
            self.score += 30
            self.flash = 24
        return None

    def draw(self, c, ctx):
        c.status("RATIO", ctx.profile.charge)
        self._gear(c, 14, 15, 6, self.driver, LEARN, self.phase)
        self._gear(c, 34, 15, 8, self.driven, CHARGE,
                   -self.phase * self.driver / self.driven)
        c.text(2, 8, str(self.driver), LEARN)
        c.text(2, 21, str(self.driven), CHARGE)
        c.text(46, 9, "WANT", DIM)
        c.text(46, 16, self._ratio(self.driver, self.want), INK)
        if self.driven == self.want:
            c.text(46, 21, "OK", GOOD)
        if self.flash:
            c.banner("LOCKED +30", GOOD)
        c.hints("DIAL", f"{self.round + 1}/5")

    def _gear(self, c, cx, cy, r, teeth, col, phase):
        """Teeth as spokes on a ring. The driven gear turns slower by exactly
        the ratio, so the lesson is visible before it is stated."""
        from math import cos, sin, pi
        n = max(6, min(16, teeth // 2))
        for i in range(n):
            a = phase + i / n * 2 * pi
            c.px(round(cx + cos(a) * r), round(cy + sin(a) * r), col)
            c.px(round(cx + cos(a) * (r - 1)), round(cy + sin(a) * (r - 1)), col)
        c.px(cx, cy, col)
