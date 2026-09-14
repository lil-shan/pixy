"""Pattern -- what comes next.

Number sequences, from counting up to doubling to Fibonacci. The explanation
names the rule, which is the part worth learning.
"""

import random
from ..canvas import INK, DIM, FAINT, CHARGE, LEARN, WIDTH, CONTENT_TOP
from .learn_base import DialGame


class Sequence(DialGame):
    key, title = "seq", "PATTERN"

    def setup(self, level):
        kinds = ["add"] if level <= 1 else \
                ["add", "sub"] if level == 2 else \
                ["add", "sub", "mul"] if level <= 4 else \
                ["add", "sub", "mul", "fib"]
        kind = random.choice(kinds)
        if kind == "add":
            step = random.randint(2, 4 + level)
            start = random.randint(1, 9)
            self.seq = [start + i * step for i in range(4)]
            self.why = "ADD %d EACH" % step
        elif kind == "sub":
            step = random.randint(2, 3 + level)
            start = step * 5 + random.randint(1, 9)
            self.seq = [start - i * step for i in range(4)]
            self.why = "TAKE %d EACH" % step
        elif kind == "mul":
            f = random.choice([2, 3])
            start = random.randint(1, 3)
            self.seq = [start * f ** i for i in range(4)]
            self.why = "TIMES %d EACH" % f
        else:
            a, b = random.randint(1, 3), random.randint(2, 5)
            self.seq = [a, b, a + b, a + 2 * b]
            self.why = "ADD LAST TWO"
        self.answer = self._next()
        self.hi = max(99, self.answer * 2)
        self.value = self.seq[-1]

    def _next(self):
        s = self.seq
        if s[1] - s[0] == s[2] - s[1]:
            return s[3] + (s[1] - s[0])
        if s[0] and s[1] % s[0] == 0 and s[1] // s[0] == s[2] // s[1]:
            return s[3] * (s[1] // s[0])
        return s[2] + s[3]

    def explain(self):
        return (self.why, "SO %d" % self.answer)

    def draw_problem(self, c, ctx):
        # The run of numbers, then a highlighted slot for the one you are
        # working out.
        text = " ".join(str(n) for n in self.seq)
        c.text_centre(CONTENT_TOP + 1, text[:15], INK)
        # Label and answer share a row, so the answer stays inside the band.
        c.text(6, CONTENT_TOP + 10, "NEXT", DIM)
        v = str(self.value)
        c.text(WIDTH - 8 - len(v) * 4, CONTENT_TOP + 10, v, CHARGE)
