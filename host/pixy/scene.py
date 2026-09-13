"""Scene stack.

Everything on screen is a Scene. update() returns a transition or None, which
keeps navigation in one place instead of scattered across games.
"""


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
        """Called when a scene pushed on top of this one popped."""
        pass


class Stack:
    def __init__(self, root, ctx):
        self.ctx = ctx
        self.scenes = [root]
        root.enter(ctx)

    @property
    def top(self):
        return self.scenes[-1]

    def update(self, s):
        act = self.top.update(s, self.ctx)
        if not act:
            return
        kind, arg = act
        if kind == "push":
            self.scenes.append(arg)
            arg.enter(self.ctx)
        elif kind == "replace":
            self.scenes[-1] = arg
            arg.enter(self.ctx)
        elif kind == "pop" and len(self.scenes) > 1:
            self.scenes.pop()
            self.top.resumed(arg, self.ctx)

    def draw(self, c):
        self.top.draw(c, self.ctx)
