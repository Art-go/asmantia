from __future__ import annotations

from Vec2 import Vec2


class Obj:
    parent: Obj
    pos: Vec2

    def __init__(self, pos: Vec2 | tuple = None, parent: Obj = None):
        if isinstance(pos, Vec2):
            self.pos = pos
        elif hasattr(pos, '__len__') and len(pos)==2:
            self.pos = Vec2.from_tuple(pos)
        elif pos is None:
            self.pos = Vec2()
        else:
            raise TypeError("pos can only be Vec2, tuple or not provided")
        self.parent = parent

    @property
    def global_pos(self):
        pos = self.pos
        if self.parent:
            pos += self.parent.global_pos
        return pos

    def render(self, *args, **kwargs):
        raise NotImplementedError

    def update(self):
        pass
