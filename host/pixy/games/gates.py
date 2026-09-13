"""Gate Keeper -- boolean logic.

A gate with two inputs and a target output. Flip inputs until the lamp matches.
Teaches AND/OR/XOR/NAND by letting a kid poke at a truth table instead of
memorising one.
"""

import random
from ..canvas import (INK, DIM, FAINT, GOOD, BAD, LEARN, CHARGE,
                      CONTENT_TOP, CONTENT_BOT)
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

KINDS = [
    ("AND",  lambda a, b: a and b),
    ("OR",   lambda a, b: a or b),
    ("XOR",  lambda a, b: a != b),
    ("NAN",  lambda a, b: not (a and b)),
    ("NOR",  lambda a, b: not (a or b)),
]
ROUNDS = 6


class Gates(Scene):
    key, title, kind = "gates", "GATE KEEPER", "learn"

    def enter(self, ctx):
        self.round = 0
        self.score = 0
        self.flash = 0
        self.new_round()

    def new_round(self):
        pool = KINDS[:2] if self.round < 2 else KINDS
        self.name, self.fn = random.choice(pool)
        self.a, self.b = random.choice([0, 1]), random.choice([0, 1])
        # Guarantee at least one flip is needed, or the puzzle solves itself.
        self.target = 0 if self.fn(self.a, self.b) else 1
        self.sel = 0
        self.solved = False

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
            ctx.deck.beep(900, 15)
            if int(bool(self.fn(self.a, self.b))) == self.target:
                self.solved = True
                self.score += 20
                self.flash = 26
                ctx.deck.beep(1700, 70)
        return None

    def draw(self, c, ctx):
        c.status(self.name, ctx.profile.charge)
        out = int(bool(self.fn(self.a, self.b)))

        # Inputs, stacked. The selected one carries a bright outline.
        for i, v in enumerate((self.a, self.b)):
            y = CONTENT_TOP + 1 + i * 9
            col = GOOD if v else BAD
            if self.sel == i:
                c.frame(0, y - 1, 9, 9, LEARN)
            c.text(3, y + 1, str(v), col)
            c.hline(9, y + 3, 5, FAINT)

        # The gate. Its name is also in the status bar; the box repeats it so
        # the eye does not have to travel.
        c.frame(14, CONTENT_TOP + 1, 16, 16, INK)
        c.text(16, CONTENT_TOP + 7, self.name, INK)
        c.hline(30, CONTENT_TOP + 8, 6, FAINT)

        # Output lamp, then the target beside it.
        ok = out == self.target
        c.frame(36, CONTENT_TOP + 5, 9, 9, GOOD if ok else DIM)
        c.text(39, CONTENT_TOP + 7, str(out), GOOD if out else BAD)

        c.text(48, CONTENT_TOP + 1, "WANT", DIM)
        c.text(54, CONTENT_TOP + 9, str(self.target), CHARGE)

        if self.solved:
            c.banner("+20", GOOD)
        c.hints("A FLIP", f"{self.round + 1}/{ROUNDS}")
