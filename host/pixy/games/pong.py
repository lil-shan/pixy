"""Pong. Two encoders, two players, one panel.

This is the game that justifies the hardware: two people, each with a dial,
on a display the size of a paperback. A d-pad cannot do this -- paddle
position tracks the wrist directly, so it plays like the original cabinet
rather than a keyboard port of it.
"""

from ..canvas import WIDTH, HEIGHT, INK, DIM, FAINT, LEARN, ARCADE, GOOD
from ..scene import Scene
from ..input import A, B

PADDLE_H, TOP, BOT = 7, 7, 25
WIN_SCORE = 7


class Pong(Scene):
    key, title, kind, cost = "pong", "PONG", "arcade", 80

    def enter(self, ctx):
        self.score = [0, 0]
        self.paddle = [(TOP + BOT) / 2 - PADDLE_H / 2] * 2
        self.serve(1)

    def serve(self, towards):
        self.ball = [WIDTH / 2, (TOP + BOT) / 2]
        self.vel = [0.7 * towards, 0.35]
        self.waiting = 18          # brief pause so nobody is caught out

    def update(self, s, ctx):
        if s.pressed(B):
            ctx.profile.record(self.key, max(self.score))
            return ("pop", {"score": max(self.score)})

        if max(self.score) >= WIN_SCORE:
            if s.pressed(A):
                self.enter(ctx)
            return None

        # One encoder each. Both paddles move on their own dial, independently.
        self.paddle[0] += s.enc(0) * 2
        self.paddle[1] += s.enc(1) * 2
        for i in (0, 1):
            self.paddle[i] = max(TOP, min(BOT - PADDLE_H, self.paddle[i]))

        if self.waiting:
            self.waiting -= 1
            return None

        self.ball[0] += self.vel[0]
        self.ball[1] += self.vel[1]

        if self.ball[1] <= TOP:
            self.ball[1], self.vel[1] = TOP, abs(self.vel[1])
        elif self.ball[1] >= BOT:
            self.ball[1], self.vel[1] = BOT, -abs(self.vel[1])

        # Paddles sit two pixels in from each edge.
        for i, px in ((0, 2), (1, WIDTH - 3)):
            if abs(self.ball[0] - px) < 1.2 and self.vel[0] * (1 if i == 0 else -1) < 0:
                py = self.paddle[i]
                if py - 1 <= self.ball[1] <= py + PADDLE_H:
                    off = (self.ball[1] - (py + PADDLE_H / 2)) / (PADDLE_H / 2)
                    self.vel[1] = max(-1.0, min(1.0, off)) * 0.7
                    self.vel[0] = -self.vel[0] * 1.04     # speeds up each rally
                    self.ball[0] = px + (1.2 if i == 0 else -1.2)

        if self.ball[0] < 0:
            self.score[1] += 1
            self.serve(1)
        elif self.ball[0] > WIDTH - 1:
            self.score[0] += 1
            self.serve(-1)
        return None

    def draw(self, c, ctx):
        c.status("PONG", ctx.profile.charge)
        for y in range(TOP, BOT, 3):
            c.px(WIDTH // 2, y, FAINT)
        c.rect(2, int(self.paddle[0]), 1, PADDLE_H, LEARN)
        c.rect(WIDTH - 3, int(self.paddle[1]), 1, PADDLE_H, ARCADE)
        c.px(int(self.ball[0]), int(self.ball[1]), INK)
        c.text(22, 0, str(self.score[0]), LEARN)
        c.text(38, 0, str(self.score[1]), ARCADE)

        if max(self.score) >= WIN_SCORE:
            who = "LEFT WINS" if self.score[0] > self.score[1] else "RIGHT WINS"
            c.banner(who, LEARN if self.score[0] > self.score[1] else ARCADE)
            c.hints("A AGAIN", "B BACK")
        else:
            c.hints("2 DIALS", "B BACK")
