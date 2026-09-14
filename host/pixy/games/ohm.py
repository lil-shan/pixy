"""Ohm's Way -- V = I x R.

Two of the three are given, dial the third. Later levels stop telling you
which formula to rearrange.
"""

import random
from ..canvas import INK, DIM, FAINT, CHARGE, LEARN, CONTENT_TOP, CONTENT_BOT
from .learn_base import DialGame


class Ohm(DialGame):
    key, title = "ohm", "OHMS WAY"

    def setup(self, level):
        # Keep the arithmetic clean at low levels; let it get awkward later.
        i = random.choice([1, 2, 3] if level <= 2 else [2, 3, 4, 5, 6])
        r = random.choice([2, 3, 4, 5] if level <= 2 else [4, 6, 8, 10, 12])
        self.i, self.r, self.v = i, r, i * r
        self.unknown = "V" if level <= 1 else random.choice(["V", "I", "R"])
        self.answer = {"V": self.v, "I": self.i, "R": self.r}[self.unknown]
        self.hi = max(60, self.answer * 3)
        self.value = 1

    def explain(self):
        if self.unknown == "V":
            return ("V = I X R", "%d X %d = %d" % (self.i, self.r, self.v))
        if self.unknown == "I":
            return ("I = V / R", "%d / %d = %d" % (self.v, self.r, self.i))
        return ("R = V / I", "%d / %d = %d" % (self.v, self.i, self.r))

    def draw_problem(self, c, ctx):
        rows = [("V", self.v, "V"), ("I", self.i, "A"), ("R", self.r, "OHM")]
        for n, (name, val, unit) in enumerate(rows):
            y = CONTENT_TOP + n * 6
            known = name != self.unknown
            c.text(3, y, name, DIM if known else LEARN)
            if known:
                c.text(16, y, str(val), INK)
                c.text(16 + len(str(val)) * 4 + 2, y, unit, FAINT)
            else:
                c.text(16, y, "?", CHARGE)
        c.text(44, CONTENT_TOP + 3, "YOU", DIM)
        c.text(44, CONTENT_TOP + 10, str(self.value), CHARGE)
