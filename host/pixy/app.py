"""Pixy console shell.

    python3 -m pixy.app 192.168.1.64

Control grammar, and it never varies:
    encoder   move through choices / set a value
    A         confirm, act
    B         back, cancel
    START     pause                (encoder 1's push)
    D-pad     direction, in games
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from panel import Panel                                    # noqa: E402
from pixy.canvas import (Canvas, INK, DIM, FAINT, CHARGE,   # noqa: E402
                         LEARN, ARCADE, GOOD, BAD)
from pixy.input import Deck, UP, DOWN, LEFT, RIGHT, A, B, START  # noqa: E402
from pixy.profile import Profile                            # noqa: E402
from pixy.scene import Scene, Stack                         # noqa: E402

from pixy.games.gates import Gates                          # noqa: E402
from pixy.games.bits import Bits                            # noqa: E402
from pixy.games.gears import Gears                          # noqa: E402
from pixy.games.snake import Snake                          # noqa: E402
from pixy.games.simon import Simon                          # noqa: E402
from pixy.games.breakout import BreakoutScene               # noqa: E402
from pixy.games.pong import Pong                            # noqa: E402

FPS = 30
LEARN_GAMES = [Gates, Bits, Gears]
ARCADE_GAMES = [BreakoutScene, Pong, Snake, Simon]


class Ctx:
    def __init__(self, profile, deck):
        self.profile = profile
        self.deck = deck


class Menu(Scene):
    """Vertical list. One row per item, one selected, scrolls when it must."""

    rows = 3

    def __init__(self, title, items, accent=INK):
        self.title, self.items, self.accent = title, items, accent
        self.sel, self.top = 0, 0

    def move(self, s):
        d = s.enc(0)
        if s.pressed(DOWN):
            d += 1
        if s.pressed(UP):
            d -= 1
        if d:
            self.sel = max(0, min(len(self.items) - 1, self.sel + d))
            self.top = max(min(self.top, self.sel), self.sel - self.rows + 1)

    def draw_rows(self, c, label_of, note_of=None):
        for i in range(self.top, min(len(self.items), self.top + self.rows)):
            y = 8 + (i - self.top) * 7
            on = i == self.sel
            if on:
                c.rect(0, y - 1, 64, 7, (18, 22, 28))
                c.text(1, y, ">", self.accent)
            c.text(6, y, label_of(i)[:12], INK if on else DIM)
            if note_of:
                n = note_of(i)
                if n:
                    c.text(64 - 1 - len(str(n)) * 4, y, str(n),
                           self.accent if on else FAINT)


class Home(Menu):
    def __init__(self):
        super().__init__("PIXY", ["LEARN", "ARCADE", "PROFILE"], CHARGE)

    def update(self, s, ctx):
        self.move(s)
        if s.pressed(A):
            if self.sel == 0:
                return ("push", LearnMenu())
            if self.sel == 1:
                return ("push", ArcadeMenu())
            return ("push", ProfileScreen())
        return None

    def draw(self, c, ctx):
        c.status("PIXY", ctx.profile.charge)
        colours = [LEARN, ARCADE, INK]
        for i, item in enumerate(self.items):
            y = 8 + i * 7
            on = i == self.sel
            if on:
                c.rect(0, y - 1, 64, 7, (18, 22, 28))
                c.text(1, y, ">", colours[i])
            c.text(6, y, item, colours[i] if on else DIM)
        c.hints("A OPEN", f"{ctx.profile.charge}")


class LearnMenu(Menu):
    def __init__(self):
        super().__init__("LEARN", LEARN_GAMES, LEARN)

    def update(self, s, ctx):
        self.move(s)
        if s.pressed(B):
            return ("pop", None)
        if s.pressed(A):
            return ("push", self.items[self.sel]())
        return None

    def draw(self, c, ctx):
        c.status("LEARN", ctx.profile.charge)
        self.draw_rows(c, lambda i: self.items[i].title,
                       lambda i: ctx.profile.level_of(self.items[i].key) or None)
        c.hints("A PLAY", "B BACK")

    def resumed(self, value, ctx):
        pass


class ArcadeMenu(Menu):
    def __init__(self):
        super().__init__("ARCADE", ARCADE_GAMES, ARCADE)

    def update(self, s, ctx):
        self.move(s)
        if s.pressed(B):
            return ("pop", None)
        if s.pressed(A):
            g = self.items[self.sel]
            if ctx.profile.unlocked(g.key):
                return ("push", g())
            if ctx.profile.unlock(g.key, g.cost):
                ctx.deck.beep(1400, 60)
                return ("push", g())
            return ("push", Toast("NEED " + str(g.cost), BAD))
        return None

    def draw(self, c, ctx):
        c.status("ARCADE", ctx.profile.charge)

        def note(i):
            g = self.items[i]
            return ctx.profile.best(g.key) if ctx.profile.unlocked(g.key) else g.cost

        self.draw_rows(c, lambda i: self.items[i].title, note)
        g = self.items[self.sel]
        c.hints("A PLAY" if ctx.profile.unlocked(g.key) else f"A UNLOCK",
                "B BACK")


class ProfileScreen(Scene):
    def update(self, s, ctx):
        if s.pressed(B) or s.pressed(A):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        c.status("PROFILE", ctx.profile.charge)
        c.text(2, 9, "CHARGE", DIM)
        c.text(40, 9, str(ctx.profile.charge), CHARGE)
        c.text(2, 16, "GAMES", DIM)
        c.text(40, 16, str(len(ctx.profile.data["unlocked"])), INK)
        best = max([ctx.profile.best(g.key) for g in ARCADE_GAMES] + [0])
        c.text(2, 22, "BEST", DIM)
        c.text(40, 22, str(best), GOOD)
        c.hints("B BACK")


class Toast(Scene):
    """Brief message, then gone. Used when an unlock is unaffordable."""

    def __init__(self, msg, col=INK, frames=40):
        self.msg, self.col, self.left = msg, col, frames

    def update(self, s, ctx):
        self.left -= 1
        if self.left <= 0 or s.pressed(A) or s.pressed(B):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        c.status("ARCADE", ctx.profile.charge)
        c.banner(self.msg, self.col)


class Results(Scene):
    """Shown after a learning game. This is where Charge is granted."""

    def __init__(self, title, charge, score):
        self.gtitle, self.charge, self.score = title, charge, score
        self.shown = 0

    def enter(self, ctx):
        if self.charge:
            ctx.profile.earn(self.charge)
            ctx.deck.beep(1600, 80)

    def update(self, s, ctx):
        self.shown += 1
        if self.shown > 12 and (s.pressed(A) or s.pressed(B)):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        c.status("RESULT", ctx.profile.charge)
        c.text_centre(9, self.gtitle[:14], DIM)
        if self.charge:
            c.text_centre(16, f"+{self.charge}", CHARGE)
            c.text_centre(22, "CHARGE", DIM)
        else:
            c.text_centre(17, "NO CHARGE", DIM)
        c.hints("A OK")


def wrap_learn(scene_cls):
    """Learning games pop a dict; turn that into a Results screen."""
    orig_update = scene_cls.update

    def update(self, s, ctx):
        act = orig_update(self, s, ctx)
        if act and act[0] == "pop" and isinstance(act[1], dict):
            r = act[1]
            return ("replace", Results(self.title, r.get("charge", 0),
                                       r.get("score", 0)))
        return act

    scene_cls.update = update
    return scene_cls


for _g in LEARN_GAMES:
    wrap_learn(_g)


def main(host):
    panel = Panel(host=host)
    panel.brightness(70)
    deck = Deck()
    ctx = Ctx(Profile(), deck)
    stack = Stack(Home(), ctx)
    print(f"Pixy up. charge={ctx.profile.charge}")

    frame = 1 / FPS
    try:
        while True:
            t0 = time.time()
            s = deck.poll()
            stack.update(s)
            c = Canvas()
            stack.draw(c)
            panel.show(c.img)
            time.sleep(max(0, frame - (time.time() - t0)))
    except KeyboardInterrupt:
        ctx.profile.save()
        panel.clear()
        print("bye")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "192.168.1.64")
