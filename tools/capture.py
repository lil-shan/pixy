import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import shoot, sheet, State                  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "host"))

import pixy.app as app                                 # noqa: E402
from pixy.profile import Profile                       # noqa: E402

p = Profile(path="/tmp/pixy_shot.json")
p.data.update({"charge": 240, "unlocked": ["breakout", "snake"], "best": {"snake": 120}})
class FD:
    def poll(self): return State(0)
    def beep(self, *a, **k): pass
ctx = app.Ctx(p, FD())

def spin(i):   # a little input so games are not frozen on frame 0
    return State((1 << 8) if i == 2 else 0)

shots = [
    ("LEARN MENU",  shoot(app.LearnMenu(), ctx)),
]
# One shot per learning game, plus each one's teach card.
for g in app.LEARN_GAMES:
    shots.append((g.title, shoot(g(), ctx, frames=6)))
for g in app.LEARN_GAMES:
    sc = g(); sc.enter(ctx)
    sc.submit(ctx, False)                 # force the explanation
    from pixy.canvas import Canvas
    sc.update(State(0), ctx)
    c = Canvas(); sc.draw(c, ctx)
    shots.append(("WHY: " + g.title, c.img))


print(sheet(shots, sys.argv[1] if len(sys.argv) > 1 else "shots.png"))
