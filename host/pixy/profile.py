"""Player progress: Charge, unlocks, best scores.

Charge is earned by learning and spent once to unlock an arcade game
permanently. Unlocks are permanent on purpose -- charging per play turns
learning into a toll booth, and a kid who runs short simply stops. A one-time
unlock gives something to work toward and then keeps giving.
"""

import json
import os

SAVE = os.path.expanduser("~/.pixy.json")

DEFAULT = {"charge": 0, "unlocked": ["breakout"], "best": {}, "solved": {}}


class Profile:
    def __init__(self, path=SAVE):
        self.path = path
        self.data = dict(DEFAULT)
        try:
            with open(path) as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f)
        except OSError:
            pass

    # ── charge ────────────────────────────────────────────────────────────
    @property
    def charge(self):
        return self.data["charge"]

    def earn(self, n):
        self.data["charge"] += int(n)
        self.save()

    def spend(self, n):
        if self.data["charge"] < n:
            return False
        self.data["charge"] -= int(n)
        self.save()
        return True

    # ── unlocks and records ───────────────────────────────────────────────
    def unlocked(self, key):
        return key in self.data["unlocked"]

    def unlock(self, key, cost):
        if self.unlocked(key):
            return True
        if not self.spend(cost):
            return False
        self.data["unlocked"].append(key)
        self.save()
        return True

    def record(self, key, score):
        """Keep the best score. Returns True when it is a new record."""
        best = self.data["best"].get(key, 0)
        if score > best:
            self.data["best"][key] = score
            self.save()
            return True
        return False

    def best(self, key):
        return self.data["best"].get(key, 0)

    def mark_solved(self, key, level):
        """Track the highest level cleared, so repeats pay less."""
        prev = self.data["solved"].get(key, 0)
        if level > prev:
            self.data["solved"][key] = level
            self.save()
            return True
        return False

    def level_of(self, key):
        return self.data["solved"].get(key, 0)
