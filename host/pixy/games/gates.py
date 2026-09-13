"""Gate Keeper -- boolean logic.

A gate with two inputs and a target output. Flip inputs until the lamp matches.
Directions pick an input, A flips it. Teaches AND/OR/XOR/NAND by letting a kid
poke at truth tables rather than memorise them.
"""

import random
from ..canvas import INK, DIM, GOOD, BAD, LEARN, CHARGE
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

KINDS = [
    ("AND",  lambda a, b: a and b),
    ("OR",   lambda a, b: a or b),
    ("XOR",  lambda a, b: a != b),
    ("NAND", lambda a, b: not (a and b)),
    ("NOR",  lambda a, b: not (a or b)),
]


class Gates(Scene):
    key, title, kind = "gates", "GATE KEEPER", "learn"

    def enter(self, ctx):
        self.round = 0
        self.score = 0
        self.new_round()
        self.flash = 0

    def new_round(self):
        # Ramp difficulty: the first rounds stay on AND/OR, later ones use all.
        pool = KINDS[:2] if self.round < 2 else KINDS
        self.name, self.fn = random.choice(pool)
        self.a, self.b = random.choice([0, 1]), random.choice([0, 1])
        # Make sure the puzzle needs at least one flip, or it solves itself.
        self.target = 1 if not self.fn(self.a, self.b) else 0
        self.sel = 0
        self.solved = False

    def update(self, s, ctx):
        if s.pressed(B):                      # START = back
            return ("pop", {"charge": self.score, "score": self.score})
        if self.flash:
            self.flash -= 1
            if self.flash == 0:
                self.round += 1
                if self.round >= 6:
                    return ("pop", {"charge": self.score, "score": self.score})
                self.new_round()
            return None

        if s.pressed(UP) or s.pressed(RIGHT):
            self.sel = 0
        if s.pressed(DOWN) or s.pressed(LEFT):
            self.sel = 1
        if s.enc(0):
            self.sel = 1 if s.enc(0) > 0 else 0
        if s.pressed(A):                      # A flips the selected input
            if self.sel == 0:
                self.a ^= 1
            else:
                self.b ^= 1
            if int(self.fn(self.a, self.b)) == self.target:
                self.solved = True
                self.score += 20
                self.flash = 24
        return None

    def draw(self, c, ctx):
        c.status(self.name, ctx.profile.charge)
        out = int(self.fn(self.a, self.b))

        for i, v in enumerate((self.a, self.b)):
            y = 10 + i * 8
            col = GOOD if v else BAD
            c.text(3, y, str(v), col)
            if self.sel == i:
                c.frame(1, y - 2, 7, 9, LEARN)
            c.hline(9, y + 2, 8, DIM)

        c.frame(18, 9, 11, 13, INK)
        c.text(21, 13, self.name[0], INK)
        c.hline(29, 15, 7, DIM)

        c.frame(37, 12, 7, 7, DIM)
        c.text(39, 13, str(out), GOOD if out else BAD)

        c.text(47, 10, "WANT", DIM)
        c.text(53, 17, str(self.target), CHARGE)

        if self.solved:
            c.banner("YES +20", GOOD)
        c.hints("A FLIP", f"{self.round + 1}/6")
