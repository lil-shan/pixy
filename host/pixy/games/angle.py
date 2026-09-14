"""Angle Hunter -- degrees.

Rotate the ray to the target angle. The dial is a protractor, which is about
as direct as a control metaphor gets, and the reason this game belongs on
hardware with a knob rather than on a touchscreen.
"""

import random
from math import cos, sin, pi
from ..canvas import INK, DIM, FAINT, GOOD, CHARGE, LEARN, CONTENT_TOP, CONTENT_BOT
from ..input import A
from .learn_base import LearnGame

# Coarser targets and a looser tolerance early on.
STEP_BY_LEVEL = [90, 45, 45, 30, 15, 15]
TOL_BY_LEVEL = [12, 10, 8, 7, 6, 5]


class Angle(LearnGame):
    key, title = "angle", "ANGLE"
    hint = "A LOCK"

    def setup(self, level):
        step = STEP_BY_LEVEL[min(level, 6) - 1]
        self.tol = TOL_BY_LEVEL[min(level, 6) - 1]
        choices = [a for a in range(step, 360, step)]
        self.target = random.choice(choices)
        self.value = 0
        self.show_number = level <= 2

    def explain(self):
        return ("THAT WAS %d" % self.value, "WANTED %d" % self.target)

    def play(self, s, ctx):
        d = s.enc(0)
        if d:
            self.value = (self.value + d * 5) % 360
            ctx.deck.beep(400 + self.value, 5)
        if s.pressed(A):
            diff = abs((self.value - self.target + 180) % 360 - 180)
            self.submit(ctx, diff <= self.tol)
        return None

    def _ray(self, c, cx, cy, r, deg, col):
        for t in range(2, r):
            a = deg * pi / 180
            c.px(round(cx + cos(a) * t), round(cy - sin(a) * t), col)

    def draw_problem(self, c, ctx):
        cx, cy, r = 20, CONTENT_TOP + 8, 8
        for deg in range(0, 360, 15):          # dial face
            a = deg * pi / 180
            c.px(round(cx + cos(a) * r), round(cy - sin(a) * r), FAINT)
        self._ray(c, cx, cy, r, self.target, DIM)
        self._ray(c, cx, cy, r, self.value, CHARGE)
        c.px(cx, cy, INK)

        c.text(38, CONTENT_TOP, "WANT", DIM)
        c.text(38, CONTENT_TOP + 6, ("%d" % self.target) if self.show_number else "? ?", INK)
        c.text(38, CONTENT_TOP + 13, "%d" % self.value, CHARGE)
