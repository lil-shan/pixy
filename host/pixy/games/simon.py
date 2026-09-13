"""Simon -- the four direction buttons are the four colours."""

import random
from ..canvas import INK, DIM, GOOD, BAD, CHARGE, LEARN, ARCADE
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

COLS = [GOOD, CHARGE, LEARN, ARCADE]          # up, down, left, right
BOXES = [(26, 8, 12, 6), (26, 20, 12, 6), (10, 14, 12, 6), (42, 14, 12, 6)]


class Simon(Scene):
    key, title, kind, cost = "simon", "SIMON", "arcade", 40

    def enter(self, ctx):
        self.reset()

    def reset(self):
        self.seq = [random.randrange(4)]
        self.step = 0
        self.showing = True
        self.timer = 0
        self.lit = None
        self.score = 0
        self.dead = False

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"score": self.score})
        if self.dead:
            if s.pressed(A):
                self.reset()
            return None

        if self.showing:
            self.timer += 1
            idx = self.timer // 14
            if idx >= len(self.seq):
                self.showing, self.lit, self.step = False, None, 0
            else:
                self.lit = self.seq[idx] if self.timer % 14 < 9 else None
            return None

        for b in range(4):
            if s.pressed(b):
                self.lit = b
                if b == self.seq[self.step]:
                    self.step += 1
                    if self.step >= len(self.seq):
                        self.score += 10
                        self.seq.append(random.randrange(4))
                        self.showing, self.timer = True, 0
                else:
                    self.dead = True
                    ctx.profile.record(self.key, self.score)
        return None

    def draw(self, c, ctx):
        c.status(f"SIMON {self.score}", ctx.profile.charge)
        for i, (x, y, w, h) in enumerate(BOXES):
            on = self.lit == i
            c.rect(x, y, w, h, COLS[i] if on else tuple(v // 5 for v in COLS[i]))
        if self.dead:
            c.banner("WRONG", BAD, f"BEST {ctx.profile.best(self.key)}")
        elif self.showing:
            c.text(1, 14, "WATCH", DIM)
        c.hints("A AGAIN" if self.dead else "REPEAT IT", f"{len(self.seq)}")
