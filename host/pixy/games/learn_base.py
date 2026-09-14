"""Shared machinery for the learning games.

Three things every learning game here does, which arcade games do not:

  * it adapts. Each game carries its own level and moves it on that game's own
    evidence, so binary can be hard while ratios stay gentle.
  * it explains. A wrong answer opens a one-line explanation of *why*, then
    puts you back on the same problem. Being told you are wrong teaches
    nothing on its own.
  * it pays more for harder work. Charge scales with level, so pushing
    yourself is worth more than farming easy rounds.
"""

from ..canvas import INK, DIM, GOOD, BAD, CHARGE, CONTENT_TOP, CONTENT_BOT
from ..scene import Scene
from ..input import UP, DOWN, LEFT, RIGHT, A, B
from ..skill import Skill

PLAY, TEACH, GOOD_ST = 0, 1, 2


class LearnGame(Scene):
    key, title, kind = "", "", "learn"
    ROUNDS = 6
    hint = "A CHECK"

    # ── subclasses implement these ────────────────────────────────────────
    def setup(self, level):
        """Build a fresh problem at this difficulty."""
        raise NotImplementedError

    def play(self, s, ctx):
        """Handle input. Call self.submit(ctx, correct) when A is pressed."""
        raise NotImplementedError

    def draw_problem(self, c, ctx):
        raise NotImplementedError

    def explain(self):
        """One or two short lines saying why the answer was wrong."""
        return ("TRY AGAIN",)

    def header(self):
        return self.title

    # ── shared ────────────────────────────────────────────────────────────
    # Solve inside this many frames (30 fps) for the full speed bonus.
    QUICK_FRAMES = 150

    def enter(self, ctx):
        self.sk = Skill(ctx.profile, self.key)
        self.round = 0
        self.score = 0
        self.tries = 0
        self.state = PLAY
        self.timer = 0
        self.elapsed = 0
        self.lines = ()
        self.msg = ""
        self.setup(self.sk.level)

    def submit(self, ctx, correct):
        if correct:
            promoted = self.sk.right(first_try=(self.tries == 0))
            # Harder levels pay more, and being quick pays more again -- so
            # pushing your level beats farming easy rounds slowly.
            bonus = max(0, 10 - int(10 * self.elapsed / self.QUICK_FRAMES))
            gain = 10 + self.sk.level * 5 + (bonus if self.tries == 0 else 0)
            self.score += gain
            self.msg = "+%d" % gain
            self.promoted = promoted
            self.state, self.timer = GOOD_ST, 30
            ctx.deck.beep(1700, 70)
        else:
            self.tries += 1
            self.sk.wrong()
            self.lines = self.explain()
            self.state, self.timer = TEACH, 70
            ctx.deck.beep(300, 80)

    def update(self, s, ctx):
        if s.pressed(B):
            return ("pop", {"charge": self.score, "score": self.score})

        if self.state == TEACH:
            self.timer -= 1
            # A dismisses early. Either way you land back on the same problem,
            # because the point is to get it right once you have been told how.
            if s.pressed(A) or self.timer <= 0:
                self.state = PLAY
            return None

        if self.state == GOOD_ST:
            self.timer -= 1
            if self.timer <= 0:
                self.round += 1
                if self.round >= self.ROUNDS:
                    ctx.profile.mark_solved(self.key, self.sk.level)
                    return ("pop", {"charge": self.score, "score": self.score})
                self.tries = 0
                self.elapsed = 0
                self.setup(self.sk.level)
                self.state = PLAY
            return None

        self.elapsed += 1
        return self.play(s, ctx)

    def draw(self, c, ctx):
        c.status(self.header(), ctx.profile.charge)
        self.draw_problem(c, ctx)
        if self.state == TEACH:
            c.teach(self.lines)
            c.hints("A GOT IT", "L%d" % self.sk.level)
        elif self.state == GOOD_ST:
            c.banner(self.msg, GOOD,
                     "LEVEL %d" % self.sk.level if getattr(self, "promoted", False) else None)
            c.hints("", "L%d" % self.sk.level)
        else:
            c.hints(self.hint, "L%d %d/%d" % (self.sk.level, self.round + 1, self.ROUNDS))


class DialGame(LearnGame):
    """A learning game whose answer is one number you dial in."""

    lo, hi, step = 0, 99, 1
    hint = "A CHECK"

    def play(self, s, ctx):
        d = s.enc(0)
        if s.pressed(RIGHT) or s.pressed(UP):
            d += 1
        if s.pressed(LEFT) or s.pressed(DOWN):
            d -= 1
        if d:
            self.value = max(self.lo, min(self.hi, self.value + d * self.step))
            ctx.deck.beep(500 + self.value * 4, 6)
        if s.pressed(A):
            self.submit(ctx, self.value == self.answer)
        return None
