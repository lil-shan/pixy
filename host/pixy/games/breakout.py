"""Breakout. Encoder steers the paddle, A serves.

A dial beats a d-pad here: the paddle tracks your wrist instead of ramping to
a fixed speed, which is the clearest argument on the console for why the
encoder is there.
"""

from ..canvas import WIDTH, HEIGHT, INK, DIM, GOOD, CHARGE, LEARN, ARCADE
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

BRICK_TOP, BRICK_ROWS, BRICK_H = 8, 4, 2
BRICK_COLS, BRICK_W = 8, 8
PADDLE_Y, PADDLE_W = 24, 9

ROW_COLOUR = [ARCADE, CHARGE, LEARN, GOOD]


class BreakoutScene(Scene):
    key, title, kind, cost = "breakout", "BREAKOUT", "arcade", 0

    def enter(self, ctx):
        self.reset(full=True)

    def reset(self, full=False):
        if full:
            self.lives, self.score = 3, 0
            self.bricks = [[True] * BRICK_COLS for _ in range(BRICK_ROWS)]
        self.paddle_x = (WIDTH - PADDLE_W) / 2
        self.ball = [WIDTH / 2, PADDLE_Y - 1.0]
        self.vel = [0.0, 0.0]
        self.stuck = True
        self.over = self.won = False

    def update(self, s, ctx):
        if s.pressed(B):                        # START exits
            ctx.profile.record(self.key, self.score)
            return ("pop", {"score": self.score})

        if self.over or self.won:
            if s.pressed(A):
                ctx.profile.record(self.key, self.score)
                self.reset(full=True)
            return None

        self.paddle_x += s.enc(0) * 2
        if s.down(LEFT):
            self.paddle_x -= 1.5
        if s.down(RIGHT):
            self.paddle_x += 1.5
        self.paddle_x = max(0, min(WIDTH - PADDLE_W, self.paddle_x))

        if self.stuck:
            self.ball = [self.paddle_x + PADDLE_W / 2, PADDLE_Y - 1.0]
            if s.pressed(A):
                self.stuck = False
                self.vel = [0.5, -0.8]
            return None

        self._step(0)
        self._step(1)

        if self.ball[1] > HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
                ctx.profile.record(self.key, self.score)
            else:
                self.reset()
        return None

    def _step(self, axis):
        """One axis at a time, so a corner hit resolves cleanly."""
        self.ball[axis] += self.vel[axis]
        x, y = self.ball
        if axis == 0:
            if x < 0:
                self.ball[0], self.vel[0] = 0, -self.vel[0]
            elif x > WIDTH - 1:
                self.ball[0], self.vel[0] = WIDTH - 1, -self.vel[0]
        elif y < 7:
            self.ball[1], self.vel[1] = 7, -self.vel[1]

        # Contact point sets the angle -- edges deflect, centre goes straight.
        if (self.vel[1] > 0 and PADDLE_Y - 1 <= y <= PADDLE_Y + 1
                and self.paddle_x - 1 <= x <= self.paddle_x + PADDLE_W):
            off = (x - (self.paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
            self.vel[0] = max(-1.0, min(1.0, off)) * 0.85
            self.vel[1] = -abs(self.vel[1])
            self.ball[1] = PADDLE_Y - 1

        bx, by = int(self.ball[0]), int(self.ball[1])
        row, col = (by - BRICK_TOP) // BRICK_H, bx // BRICK_W
        if 0 <= row < BRICK_ROWS and 0 <= col < BRICK_COLS and self.bricks[row][col]:
            self.bricks[row][col] = False
            self.score += (BRICK_ROWS - row) * 10
            self.vel[axis] = -self.vel[axis]
            if not any(any(r) for r in self.bricks):
                self.won = True

    def draw(self, c, ctx):
        c.status(f"BALL {self.lives}", ctx.profile.charge)
        for r, row in enumerate(self.bricks):
            for col, alive in enumerate(row):
                if alive:
                    c.rect(col * BRICK_W, BRICK_TOP + r * BRICK_H,
                           BRICK_W - 1, BRICK_H - 1, ROW_COLOUR[r])
        c.rect(int(self.paddle_x), PADDLE_Y, PADDLE_W, 1, (150, 200, 255))
        c.px(int(self.ball[0]), int(self.ball[1]), INK)
        if self.over or self.won:
            c.banner("CLEARED" if self.won else "GAME OVER",
                     GOOD if self.won else ARCADE, f"BEST {ctx.profile.best(self.key)}")
        c.hints("A SERVE" if self.stuck else str(self.score), "B BACK")
