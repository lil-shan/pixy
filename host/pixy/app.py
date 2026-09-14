"""Pixy console shell.

    python3 -m pixy.app 192.168.1.64

Control grammar. It never varies, anywhere:

    dial      move through choices / set a value
    A         confirm, act
    B         back, cancel
    d-pad     direction, inside games

There is one dial. The second encoder was removed from the hardware, so
nothing here refers to it.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from panel import Panel                                          # noqa: E402
from pixy.canvas import (Canvas, INK, DIM, FAINT, CHARGE, LEARN,  # noqa: E402
                         ARCADE, GOOD, BAD, WIDTH, CONTENT_TOP,
                         CONTENT_BOT, ROW_H, ROWS)
from pixy.input import Deck, UP, DOWN, LEFT, RIGHT, A, B, START   # noqa: E402
from pixy.profile import Profile                                  # noqa: E402
from pixy.scene import Scene, Stack                               # noqa: E402

from pixy.games.gates import Gates                                # noqa: E402
from pixy.games.bits import Bits                                  # noqa: E402
from pixy.games.gears import Gears                                # noqa: E402
from pixy.games.ohm import Ohm                                    # noqa: E402
from pixy.games.sequence import Sequence                          # noqa: E402
from pixy.games.angle import Angle                                # noqa: E402
from pixy.games.snake import Snake                                # noqa: E402
from pixy.games.simon import Simon                                # noqa: E402
from pixy.games.breakout import BreakoutScene                     # noqa: E402
from pixy.games.pong import Pong                                  # noqa: E402

FPS = 30
LEARN_GAMES = [Gates, Bits, Sequence, Ohm, Gears, Angle]
ARCADE_GAMES = [BreakoutScene, Pong, Snake, Simon]

# Two lines each, max 15 characters, shown before every game. Nobody should
# have to guess which button does what on a device with unlabelled controls.
HELP = {
    "gates":    ("PICK AN INPUT", "A FLIPS IT"),
    "bits":     ("DIAL PICKS BIT", "A FLIPS IT"),
    "seq":      ("WHAT COMES", "NEXT? DIAL IT"),
    "ohm":      ("FIND THE", "MISSING VALUE"),
    "gears":    ("MATCH THE", "GEAR RATIO"),
    "angle":    ("TURN TO THE", "RIGHT ANGLE"),
    "breakout": ("DIAL = PADDLE", "A SERVES"),
    "pong":     ("DIAL = PADDLE", "UP DOWN = P2"),
    "snake":    ("D-PAD STEERS", "EAT THE DOTS"),
    "simon":    ("WATCH, REPEAT", "USE THE D-PAD"),
}


class Ctx:
    def __init__(self, profile, deck):
        self.profile = profile
        self.deck = deck


# ── Menus ─────────────────────────────────────────────────────────────────
class Menu(Scene):
    """Vertical list. Exactly ROWS rows fit the content band; anything more
    scrolls, with arrows so it is obvious there is more."""

    def __init__(self, title, items, accent=INK):
        self.title, self.items, self.accent = title, items, accent
        self.sel, self.top = 0, 0

    def move(self, s):
        d = s.enc(0)
        if s.pressed(DOWN):
            d += 1
        if s.pressed(UP):
            d -= 1
        if not d:
            return
        self.sel = max(0, min(len(self.items) - 1, self.sel + d))
        # Keep the selection inside the window.
        self.top = min(self.top, self.sel)
        self.top = max(self.top, self.sel - ROWS + 1)
        self.top = max(0, min(self.top, max(0, len(self.items) - ROWS)))

    def draw_rows(self, c, ctx, label_of, note_of=None, colour_of=None):
        # Reserve the arrow column only when the list actually scrolls.
        pad = c.SCROLL_W + 2 if len(self.items) > ROWS else 1
        for i in range(self.top, min(len(self.items), self.top + ROWS)):
            y = CONTENT_TOP + (i - self.top) * ROW_H
            on = i == self.sel
            col = colour_of(i) if colour_of else self.accent
            # Selected row: bright caret in the accent, label at full white.
            # Unselected: no marker, dimmer label. No background fill.
            if on:
                c.text(0, y, ">", col)
                c.text(5, y, label_of(i)[:11], INK)
            else:
                c.text(5, y, label_of(i)[:11], DIM)
            if note_of:
                n = note_of(i)
                if n is not None:
                    t = str(n)
                    c.text(WIDTH - pad - len(t) * 4, y, t, col if on else FAINT)
        c.scroll_marks(self.top, ROWS, len(self.items))


class Home(Menu):
    COLOURS = [LEARN, ARCADE, INK]

    def __init__(self):
        super().__init__("PIXY", ["LEARN", "ARCADE", "PROFILE"], CHARGE)

    def update(self, s, ctx):
        self.move(s)
        if s.pressed(A):
            return ("push", [LearnMenu, ArcadeMenu, ProfileScreen][self.sel]())
        return None

    def draw(self, c, ctx):
        c.status("PIXY", ctx.profile.charge)
        self.draw_rows(c, ctx, lambda i: self.items[i],
                       colour_of=lambda i: self.COLOURS[i])
        c.hints("A OPEN", f"{ctx.profile.charge}")


class LearnMenu(Menu):
    def __init__(self):
        super().__init__("LEARN", LEARN_GAMES, LEARN)

    def update(self, s, ctx):
        self.move(s)
        if s.pressed(B):
            return ("pop", None)
        if s.pressed(A):
            return ("push", Help(self.items[self.sel]))
        return None

    def draw(self, c, ctx):
        c.status("LEARN", ctx.profile.charge)
        def lvl(i):
            st = ctx.profile.data.get("skill", {}).get(self.items[i].key)
            return ("L%d" % st["lvl"]) if st else None

        self.draw_rows(c, ctx, lambda i: self.items[i].title, lvl)
        c.hints("A PLAY", "B BACK")


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
                return ("push", Help(g))
            if ctx.profile.unlock(g.key, g.cost):
                ctx.deck.beep(1400, 60)
                return ("push", Help(g))
            return ("push", Toast(f"NEED {g.cost}", BAD))
        return None

    def draw(self, c, ctx):
        c.status("ARCADE", ctx.profile.charge)

        def note(i):
            g = self.items[i]
            return ctx.profile.best(g.key) if ctx.profile.unlocked(g.key) else g.cost

        self.draw_rows(c, ctx, lambda i: self.items[i].title, note)
        g = self.items[self.sel]
        c.hints("A PLAY" if ctx.profile.unlocked(g.key) else "A UNLOCK", "B BACK")


class ProfileScreen(Scene):
    def update(self, s, ctx):
        if s.pressed(B) or s.pressed(A):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        c.status("PROFILE", ctx.profile.charge)
        rows = [("CHARGE", ctx.profile.charge, CHARGE),
                ("GAMES", len(ctx.profile.data["unlocked"]), INK),
                ("BEST", max([ctx.profile.best(g.key) for g in ARCADE_GAMES] + [0]), GOOD)]
        for i, (label, value, col) in enumerate(rows):
            y = CONTENT_TOP + i * ROW_H
            c.text(2, y, label, DIM)
            t = str(value)
            c.text(WIDTH - 2 - len(t) * 4, y, t, col)
        c.hints("B BACK")


class Toast(Scene):
    def __init__(self, msg, col=INK, frames=45):
        self.msg, self.col, self.left = msg, col, frames

    def update(self, s, ctx):
        self.left -= 1
        if self.left <= 0 or s.pressed(A) or s.pressed(B):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        c.status("ARCADE", ctx.profile.charge)
        c.banner(self.msg, self.col)
        c.hints("LEARN TO EARN")


class Help(Scene):
    """Shown briefly before a game. Auto-advances so repeat plays are not
    slowed down, but A skips it instantly."""

    def __init__(self, game_cls, frames=75):
        self.game_cls, self.left = game_cls, frames

    def update(self, s, ctx):
        self.left -= 1
        if self.left <= 0 or s.pressed(A):
            return ("replace", self.game_cls())
        if s.pressed(B):
            return ("pop", None)
        return None

    def draw(self, c, ctx):
        g = self.game_cls
        accent = LEARN if g.kind == "learn" else ARCADE
        c.status(g.title, ctx.profile.charge)
        c.card(HELP.get(g.key, ("", "")), accent)
        # Thin bar showing it will start on its own. Sits on the last content
        # row, clear of both help lines.
        bar = int((1 - self.left / 75) * (WIDTH - 4))
        c.hline(2, CONTENT_BOT, max(1, bar), FAINT)
        c.hints("A START", "B BACK")


class Results(Scene):
    """After a learning game. This is where Charge is granted."""

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
        c.text_centre(CONTENT_TOP, self.gtitle[:15], DIM)
        if self.charge:
            c.text_centre(CONTENT_TOP + 6, f"+{self.charge}", CHARGE)
            c.text_centre(CONTENT_TOP + 12, "CHARGE", DIM)
        else:
            c.text_centre(CONTENT_TOP + 9, "NO CHARGE", DIM)
        c.hints("A OK")


# ── Tutorial ──────────────────────────────────────────────────────────────
class Tutorial(Scene):
    """Teaches the three controls by making you use each one. Runs once, then
    is reachable again from Profile if anyone wants it."""

    STEPS = [
        ("TURN THE DIAL", "dial"),
        ("PRESS A", "a"),
        ("PRESS B", "b"),
    ]

    def enter(self, ctx):
        self.step = 0
        self.progress = 0
        self.done_at = None

    def update(self, s, ctx):
        if self.done_at is not None:
            self.done_at += 1
            if self.done_at > 40:
                ctx.profile.data["tutorial"] = True
                ctx.profile.save()
                return ("pop", None)
            return None

        kind = self.STEPS[self.step][1]
        hit = ((kind == "dial" and s.enc(0) != 0)
               or (kind == "a" and s.pressed(A))
               or (kind == "b" and s.pressed(B)))
        if kind == "dial" and s.enc(0):
            self.progress += abs(s.enc(0))
            hit = self.progress >= 3
        if hit:
            ctx.deck.beep(1200 + self.step * 200, 40)
            self.step += 1
            self.progress = 0
            if self.step >= len(self.STEPS):
                self.done_at = 0
        return None

    def draw(self, c, ctx):
        c.status("HOW TO PLAY")
        if self.done_at is not None:
            c.banner("READY", GOOD)
            c.hints("THAT IS ALL")
            return
        label, kind = self.STEPS[self.step]
        c.text_centre(CONTENT_TOP + 2, label, INK)
        # One dot per step, filled as you go, so progress is obvious.
        for i in range(len(self.STEPS)):
            x = WIDTH // 2 - 8 + i * 8
            if i < self.step:
                c.rect(x, CONTENT_TOP + 11, 5, 5, GOOD)
            else:
                c.frame(x, CONTENT_TOP + 11, 5, 5, DIM if i == self.step else FAINT)
        c.hints(f"STEP {self.step + 1}/3", "ANY WAY" if kind == "dial" else None)


def wrap_learn(scene_cls):
    """Learning games pop a dict; turn that into a Results screen."""
    orig = scene_cls.update

    def update(self, s, ctx):
        act = orig(self, s, ctx)
        if act and act[0] == "pop" and isinstance(act[1], dict):
            r = act[1]
            return ("replace", Results(self.title, r.get("charge", 0), r.get("score", 0)))
        return act

    scene_cls.update = update
    return scene_cls


for _g in LEARN_GAMES:
    wrap_learn(_g)


def main(host, seconds=None):
    panel = Panel(host=host)
    panel.brightness(70)
    deck = Deck()
    ctx = Ctx(Profile(), deck)
    root = Home()
    stack = Stack(root, ctx)
    if not ctx.profile.data.get("tutorial"):
        stack.scenes.append(Tutorial())
        stack.top.enter(ctx)
    print(f"Pixy up. charge={ctx.profile.charge}")

    frame = 1 / FPS
    deadline = time.time() + seconds if seconds else None
    try:
        while deadline is None or time.time() < deadline:
            t0 = time.time()
            stack.update(deck.poll())
            c = Canvas()
            stack.draw(c)
            panel.show(c.img)
            time.sleep(max(0, frame - (time.time() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        ctx.profile.save()
        panel.clear()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "192.168.1.64",
         float(sys.argv[2]) if len(sys.argv) > 2 else None)
