"""Angle Hunter -- degrees by eye.

You are told the angle and you have to *find* it. There is no target ray to
line up against and, past the first level, no readout of where you currently
are -- otherwise it collapses into matching two numbers, which teaches
nothing about what 130 degrees looks like.

The dial is a protractor. That is the whole reason this game belongs on
hardware with a knob.
"""

import random
from math import cos, sin, pi
from ..canvas import INK, DIM, FAINT, GOOD, CHARGE, LEARN, CONTENT_TOP, CONTENT_BOT
from ..input import A
from .learn_base import LearnGame

# Tolerance in degrees, by level. Level 8 is within 3 degrees by eye.
TOL = [16, 13, 11, 9, 7, 6, 4, 3]


class Angle(LearnGame):
    key, title = "angle", "ANGLE"
    hint = "A LOCK"

    def setup(self, level):
        lv = min(level, 8)
        self.tol = TOL[lv - 1]
        if lv <= 2:                     # the familiar quarters
            step = 45
            self.target = random.choice([a for a in range(step, 360, step)])
        elif lv <= 4:
            self.target = random.choice([a for a in range(15, 360, 15)])
        else:                           # anything at all
            self.target = random.randint(5, 355)
        # Never start on the answer, and start somewhere different each time.
        self.value = (self.target + random.randint(60, 300)) % 360
        self.show_value = lv <= 1
        self.locked = None

    def explain(self):
        off = (self.value - self.target + 180) % 360 - 180
        way = "RIGHT" if off > 0 else "LEFT"
        return ("YOU WERE %d" % self.value, "%d SHORT %s" % (abs(off), way))

    def play(self, s, ctx):
        d = s.enc(0)
        if d:
            self.value = (self.value + d * 3) % 360
            ctx.deck.beep(400 + self.value, 4)
        if s.pressed(A):
            diff = abs((self.value - self.target + 180) % 360 - 180)
            self.locked = self.value
            self.submit(ctx, diff <= self.tol)
        return None

    def _ray(self, c, cx, cy, r, deg, col, start=2):
        a = deg * pi / 180
        for t in range(start, r):
            c.px(round(cx + cos(a) * t), round(cy - sin(a) * t), col)

    def draw_problem(self, c, ctx):
        cx, cy, r = 20, CONTENT_TOP + 8, 9
        # Dial face. Cardinals are brighter so there is *some* reference,
        # which is how a real protractor works.
        for deg in range(0, 360, 15):
            a = deg * pi / 180
            col = DIM if deg % 90 == 0 else FAINT
            c.px(round(cx + cos(a) * r), round(cy - sin(a) * r), col)
        self._ray(c, cx, cy, r, self.value, CHARGE)
        c.px(cx, cy, INK)

        c.text(38, CONTENT_TOP + 1, "FIND", DIM)
        c.text(38, CONTENT_TOP + 8, "%d" % self.target, INK)
        if self.show_value:
            c.text(38, CONTENT_TOP + 15, "%d" % self.value, CHARGE)
        else:
            c.text(38, CONTENT_TOP + 15, "+-%d" % self.tol, FAINT)
