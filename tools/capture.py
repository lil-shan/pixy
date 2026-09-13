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
    ("HOME",        shoot(app.Home(), ctx)),
    ("LEARN MENU",  shoot(app.LearnMenu(), ctx)),
    ("ARCADE MENU", shoot(app.ArcadeMenu(), ctx)),
    ("PROFILE",     shoot(app.ProfileScreen(), ctx)),
    ("RESULTS",     shoot(app.Results("GATE KEEPER", 40, 40), ctx)),
    ("TOAST",       shoot(app.Toast("NEED 80"), ctx)),
]
shots.append(("HELP CARD", shoot(app.Help(app.LEARN_GAMES[0]), ctx, frames=20)))
shots.append(("TUTORIAL 1", shoot(app.Tutorial(), ctx, frames=2)))
def turn(i):
    return State((2 << 16)) if i in (3, 5, 7) else State(0)
shots.append(("TUTORIAL 2", shoot(app.Tutorial(), ctx, frames=9, feed=turn)))
for g in app.LEARN_GAMES + app.ARCADE_GAMES:
    shots.append((g.title, shoot(g(), ctx, frames=40, feed=spin)))

print(sheet(shots, sys.argv[1] if len(sys.argv) > 1 else "shots.png"))
