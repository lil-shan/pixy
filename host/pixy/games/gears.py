"""Gear Lab -- ratios.

Dial the driven gear until the ratio matches the target. Both wheels turn, and
the driven one turns slower by exactly the ratio, so the lesson is visible
before it is stated. One dial: the driver gear is fixed each round.
"""

import random
from math import gcd, cos, sin, pi
from ..canvas import (INK, DIM, FAINT, GOOD, CHARGE, LEARN,
                      CONTENT_TOP, CONTENT_BOT)
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B

ROUNDS = 5


class Gears(Scene):
    key, title, kind = "gears", "GEAR LAB", "learn"

    def enter(self, ctx):
        self.round, self.score, self.flash = 0, 0, 0
        self.phase = 0.0
        self.new_round()

    def new_round(self):
        self.driver = random.choice([8, 10, 12])
        self.mult = random.choice([2, 3]) if self.round < 2 else random.choice([2, 3, 4])
        self.want = self.driver * self.mult
        self.driven = self.driver

    def ratio_text(self, a, b):
        g = gcd(a, b)
        return "%d:%d" % (a // g, b // g)

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"charge": self.score, "score": self.score})
        self.phase += 3.0
        if self.flash:
            self.flash -= 1
            if self.flash == 0:
                self.round += 1
                if self.round >= ROUNDS:
                    ctx.profile.mark_solved(self.key, self.round)
                    return ("pop", {"charge": self.score, "score": self.score})
                self.new_round()
            return None

        step = s.enc(0)
        if s.pressed(RIGHT) or s.pressed(UP):
            step += 1
        if s.pressed(LEFT) or s.pressed(DOWN):
            step -= 1
        if step:
            self.driven = max(4, min(60, self.driven + step))
            ctx.deck.beep(500 + self.driven * 8, 8)

        if s.pressed(A):
            if self.driven == self.want:
                self.score += 30
                self.flash = 26
                ctx.deck.beep(1700, 70)
            else:
                ctx.deck.beep(300, 60)
        return None

    def wheel(self, c, cx, cy, r, teeth, col, phase):
        """A solid rim with teeth standing off it, plus a hub. Teeth alone
        read as scattered dots at this size -- the rim is what makes the eye
        see a gear."""
        dim = tuple(v // 3 for v in col)
        for deg in range(0, 360, 8):           # rim
            a = deg * pi / 180
            c.px(round(cx + cos(a) * r), round(cy + sin(a) * r), dim)
        n = max(5, min(12, teeth))
        for i in range(n):                     # teeth
            a = (phase + i * 360.0 / n) * pi / 180
            c.px(round(cx + cos(a) * (r + 1)), round(cy + sin(a) * (r + 1)), col)
        c.px(cx, cy, col)                      # hub

    def draw(self, c, ctx):
        c.status("GEAR LAB", ctx.profile.charge)
        mid = CONTENT_TOP + 5

        self.wheel(c, 9, mid, 4, self.driver, LEARN, self.phase)
        self.wheel(c, 25, mid, 5, self.driven, CHARGE,
                   -self.phase * self.driver / max(1, self.driven))

        # Counts get their own row under the wheels rather than sitting on them.
        c.text(5, CONTENT_BOT - 4, str(self.driver), LEARN)
        c.text(22, CONTENT_BOT - 4, str(self.driven), CHARGE)

        ok = self.driven == self.want
        c.text(40, CONTENT_TOP, "WANT", DIM)
        c.text(40, CONTENT_TOP + 7, self.ratio_text(self.driver, self.want), INK)
        c.text(40, CONTENT_TOP + 14, "OK" if ok else "..", GOOD if ok else FAINT)

        if self.flash:
            c.banner("+30", GOOD)
        c.hints("A LOCK", "%d/%d" % (self.round + 1, ROUNDS))
