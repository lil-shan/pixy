"""Scene stack, with transitions.

Everything on screen is a Scene. update() returns a transition or None, which
keeps navigation in one place instead of scattered through the games.

Pushing slides the new screen in from the right, popping slides it back out.
That is not decoration: on a 64x32 panel with no window chrome, a cut between
two screens is genuinely disorienting, and the direction of travel is what
tells you whether you went deeper or came back.
"""

ANIM_FRAMES = 5          # ~170 ms at 30 fps. Long enough to read, short
                         # enough that nobody waits for it.


class Scene:
    title = ""

    def enter(self, ctx):
        pass

    def update(self, s, ctx):
        """Return None, or ("push", scene) / ("pop", value) / ("replace", scene)."""
        return None

    def draw(self, c, ctx):
        raise NotImplementedError

    def resumed(self, value, ctx):
        """Called when a scene pushed on top of this one has popped."""
        pass


class Stack:
    def __init__(self, root, ctx):
        self.ctx = ctx
        self.scenes = [root]
        self.anim = 0
        self.anim_dir = 1
        self.prev_img = None
        self.last_img = None
        root.enter(ctx)

    @property
    def top(self):
        return self.scenes[-1]

    def _begin_anim(self, direction):
        self.prev_img = self.last_img
        self.anim = ANIM_FRAMES if self.prev_img is not None else 0
        self.anim_dir = direction

    def update(self, s):
        act = self.top.update(s, self.ctx)
        if not act:
            return
        kind, arg = act
        if kind == "push":
            self._begin_anim(1)
            self.scenes.append(arg)
            arg.enter(self.ctx)
        elif kind == "replace":
            self._begin_anim(1)
            self.scenes[-1] = arg
            arg.enter(self.ctx)
        elif kind == "pop" and len(self.scenes) > 1:
            self._begin_anim(-1)
            self.scenes.pop()
            self.top.resumed(arg, self.ctx)

    def draw(self, c):
        self.top.draw(c, self.ctx)
        if self.anim > 0 and self.prev_img is not None:
            w, h = c.img.size
            incoming = c.img.copy()
            frac = self.anim / float(ANIM_FRAMES)
            dx = int(round(w * frac)) * self.anim_dir
            c.d.rectangle([0, 0, w, h], fill=(0, 0, 0))
            c.img.paste(self.prev_img, (dx - w * self.anim_dir, 0))
            c.img.paste(incoming, (dx, 0))
            self.anim -= 1
        self.last_img = c.img.copy()
