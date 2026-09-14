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
        lv = min(level, 8)
        kinds = (["add"] if lv <= 1 else
                 ["add", "sub"] if lv == 2 else
                 ["add", "sub", "mul"] if lv <= 4 else
                 ["add", "sub", "mul", "fib"] if lv <= 6 else
                 ["add", "sub", "mul", "fib", "sq", "ramp"])
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
        elif kind == "fib":
            a, b = random.randint(1, 4), random.randint(2, 6)
            self.seq = [a, b, a + b, a + 2 * b]
            self.why = "ADD LAST TWO"
        elif kind == "sq":
            start = random.randint(1, 4)
            self.seq = [(start + i) ** 2 for i in range(4)]
            self.why = "SQUARE NUMBERS"
        else:                                   # gap grows each step
            start = random.randint(1, 6)
            g = random.randint(1, 3)
            vals, cur, gap = [], start, g
            for _ in range(4):
                vals.append(cur)
                cur += gap
                gap += g
            self.seq = vals
            self.why = "GAP GROWS BY %d" % g
        self.answer = self._next()
        self.hi = max(99, self.answer * 2)
        self.value = self.seq[-1]

    def _next(self):
        """Work the next term out from the sequence itself, so a new pattern
        kind cannot silently disagree with its own answer."""
        s = self.seq
        d = [s[i + 1] - s[i] for i in range(3)]
        if d[0] == d[1] == d[2]:                       # constant step
            return s[3] + d[0]
        if d[1] - d[0] == d[2] - d[1]:                 # step grows evenly
            return s[3] + d[2] + (d[1] - d[0])
        if s[0] and all(s[i + 1] % s[i] == 0 for i in range(3)) \
                and len({s[i + 1] // s[i] for i in range(3)}) == 1:
            return s[3] * (s[1] // s[0])
        return s[2] + s[3]                             # fibonacci-ish

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
