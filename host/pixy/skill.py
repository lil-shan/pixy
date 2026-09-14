"""Per-game adaptive difficulty.

Each learning game carries its own level, and each advances on its own
evidence. A kid who has binary cold but finds ratios hard should be getting
hard binary and gentle ratios at the same time -- a single global "difficulty"
would hold one back while overwhelming the other.

The rule is deliberately simple, because it has to be legible to whoever
tunes it later:

    two first-try corrects in a row   -> level up
    two wrong answers in a row        -> level down
    anything else                     -> stay, and reset the counters

First-try matters. Getting there after three wrong guesses is not the same as
knowing it, so only a clean answer counts toward promotion.
"""

MIN_LEVEL = 1
MAX_LEVEL = 6
PROMOTE_AT = 2
DEMOTE_AT = 2


class Skill:
    def __init__(self, profile, key):
        self.profile = profile
        self.key = key
        store = profile.data.setdefault("skill", {})
        self.state = store.setdefault(key, {"lvl": MIN_LEVEL, "up": 0, "dn": 0,
                                            "seen": 0, "correct": 0})

    @property
    def level(self):
        return max(MIN_LEVEL, min(MAX_LEVEL, int(self.state.get("lvl", MIN_LEVEL))))

    @property
    def accuracy(self):
        seen = self.state.get("seen", 0)
        return self.state["correct"] / seen if seen else 0.0

    def right(self, first_try=True):
        """Record a correct answer. Returns True if the level went up."""
        self.state["seen"] += 1
        self.state["correct"] += 1
        if not first_try:
            self.state["up"] = 0
            self.state["dn"] = 0
            self._save()
            return False
        self.state["dn"] = 0
        self.state["up"] += 1
        promoted = False
        if self.state["up"] >= PROMOTE_AT and self.level < MAX_LEVEL:
            self.state["lvl"] = self.level + 1
            self.state["up"] = 0
            promoted = True
        self._save()
        return promoted

    def wrong(self):
        """Record a wrong answer. Returns True if the level went down."""
        self.state["seen"] += 1
        self.state["up"] = 0
        self.state["dn"] += 1
        demoted = False
        if self.state["dn"] >= DEMOTE_AT and self.level > MIN_LEVEL:
            self.state["lvl"] = self.level - 1
            self.state["dn"] = 0
            demoted = True
        self._save()
        return demoted

    def _save(self):
        self.profile.data.setdefault("skill", {})[self.key] = self.state
        self.profile.save()
