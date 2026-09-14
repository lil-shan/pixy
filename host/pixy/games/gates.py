"""Gate Keeper -- boolean logic, adaptive.

Past level 5 the gate stops telling you what it is. You flip inputs, watch the
output, work out what it must be, then drive it to the target. That turns it
from recall into the thing you actually want a kid doing: forming a hypothesis
and testing it.
"""

import random
from ..canvas import INK, DIM, FAINT, GOOD, BAD, LEARN, CHARGE, CONTENT_TOP
from ..input import UP, DOWN, LEFT, RIGHT, A
from .learn_base import LearnGame

KINDS = {
    "AND": (lambda a, b: a and b,       "BOTH MUST BE 1"),
    "OR":  (lambda a, b: a or b,        "EITHER ONE 1"),
    "XOR": (lambda a, b: a != b,        "ONE, NOT BOTH"),
    "NAN": (lambda a, b: not (a and b), "AND, FLIPPED"),
    "NOR": (lambda a, b: not (a or b),  "OR, FLIPPED"),
}
BY_LEVEL = [
    ["AND", "OR"], ["AND", "OR"], ["AND", "OR", "XOR"],
    ["AND", "OR", "XOR", "NAN"], ["AND", "OR", "XOR", "NAN", "NOR"],
    ["AND", "OR", "XOR", "NAN", "NOR"], ["AND", "OR", "XOR", "NAN", "NOR"],
    ["AND", "OR", "XOR", "NAN", "NOR"],
]
HIDE_FROM = 5


class Gates(LearnGame):
    key, title = "gates", "GATES"
    hint = "A FLIP"

    def setup(self, level):
        lv = min(level, 8)
        self.name = random.choice(BY_LEVEL[lv - 1])
        self.fn, self.why = KINDS[self.name]
        self.hidden = lv >= HIDE_FROM
        # Target is genuinely random, not just "whatever you are not showing".
        # Re-roll the inputs until the puzzle actually needs work.
        for _ in range(20):
            self.a, self.b = random.choice([0, 1]), random.choice([0, 1])
            self.target = random.choice([0, 1])
            if int(bool(self.fn(self.a, self.b))) != self.target:
                break
        self.sel = 0

    def header(self):
        return "?" if self.hidden else self.name

    def explain(self):
        return (self.name + " -> " + str(self.target), self.why)

    def play(self, s, ctx):
        if s.pressed(UP) or s.pressed(LEFT):
            self.sel = 0
        if s.pressed(DOWN) or s.pressed(RIGHT):
            self.sel = 1
        if s.enc(0):
            self.sel = 1 if s.enc(0) > 0 else 0
        if s.pressed(A):
            if self.sel == 0:
                self.a ^= 1
            else:
                self.b ^= 1
            ctx.deck.beep(900, 12)
            if int(bool(self.fn(self.a, self.b))) == self.target:
                self.submit(ctx, True)
        return None

    def draw_problem(self, c, ctx):
        out = int(bool(self.fn(self.a, self.b)))
        for i, v in enumerate((self.a, self.b)):
            y = CONTENT_TOP + 1 + i * 9
            if self.sel == i:
                c.frame(0, y - 1, 9, 9, LEARN)
            c.text(3, y + 1, str(v), GOOD if v else BAD)
            c.hline(9, y + 3, 5, FAINT)
        c.frame(14, CONTENT_TOP + 1, 16, 16, INK)
        label = "?" if self.hidden else self.name
        c.text(16 if not self.hidden else 20, CONTENT_TOP + 7, label, INK)
        c.hline(30, CONTENT_TOP + 8, 6, FAINT)
        c.frame(36, CONTENT_TOP + 5, 9, 9, DIM)
        c.text(39, CONTENT_TOP + 7, str(out), GOOD if out else BAD)
        c.text(48, CONTENT_TOP + 1, "WANT", DIM)
        c.text(54, CONTENT_TOP + 9, str(self.target), CHARGE)
