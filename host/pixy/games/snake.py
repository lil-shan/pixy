"""Snake. Directions steer, A restarts."""

import random
from ..canvas import GOOD, ARCADE, INK, DIM
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

W, H = 64, 19          # play area sits between the status and hint bars
TOP = 7


class Snake(Scene):
    key, title, kind, cost = "snake", "SNAKE", "arcade", 60

    def enter(self, ctx):
        self.reset()

    def reset(self):
        self.body = [(10, 9), (9, 9), (8, 9)]
        self.dir = (1, 0)
        self.pending = self.dir
        self.food = self.place()
        self.score = 0
        self.dead = False
        self.tick = 0

    def place(self):
        while True:
            p = (random.randrange(W), random.randrange(H))
            if p not in self.body:
                return p

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"score": self.score})
        if self.dead:
            if s.pressed(A):
                self.reset()
            return None

        # Queue the turn rather than applying it immediately, so two presses
        # inside one tick cannot fold the snake back into itself.
        dx, dy = self.dir
        if s.pressed(UP) and dy == 0:
            self.pending = (0, -1)
        elif s.pressed(DOWN) and dy == 0:
            self.pending = (0, 1)
        elif s.pressed(LEFT) and dx == 0:
            self.pending = (-1, 0)
        elif s.pressed(RIGHT) and dx == 0:
            self.pending = (1, 0)

        self.tick += 1
        speed = max(3, 7 - self.score // 40)
        if self.tick % speed:
            return None

        self.dir = self.pending
        hx, hy = self.body[0]
        head = ((hx + self.dir[0]) % W, (hy + self.dir[1]) % H)
        if head in self.body:
            self.dead = True
            ctx.profile.record(self.key, self.score)
            return None
        self.body.insert(0, head)
        if head == self.food:
            self.score += 10
            self.food = self.place()
        else:
            self.body.pop()
        return None

    def draw(self, c, ctx):
        c.status(f"SNAKE {self.score}", ctx.profile.charge)
        c.px(self.food[0], TOP + self.food[1], ARCADE)
        for i, (x, y) in enumerate(self.body):
            c.px(x, TOP + y, INK if i == 0 else GOOD)
        if self.dead:
            c.banner("GAME OVER", ARCADE, f"BEST {ctx.profile.best(self.key)}")
        c.hints("A AGAIN" if self.dead else None, "B BACK")
