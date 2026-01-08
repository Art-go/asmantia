from __future__ import annotations

from .vec2 import Vec2


class Obj:
    _parent: Obj | None
    pos: Vec2
    children: set[Obj]

    def __init__(self, pos: Vec2 | tuple = None, parent: Obj = None):
        if isinstance(pos, Vec2):
            self.pos = pos
        elif hasattr(pos, '__len__') and len(pos) == 2:
            self.pos = Vec2.from_tuple(pos)
        elif pos is None:
            self.pos = Vec2()
        else:
            raise TypeError("pos can only be Vec2, tuple or not provided")
        self.children = set()
        self._parent = None
        self.parent = parent

    @property
    def global_pos(self):
        pos = self.pos
        if self.parent:
            pos += self.parent.global_pos
        return pos

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, new_parent: Obj):
        if self._parent is not None:
            self._parent.children.remove(self)
        self._parent = new_parent
        if new_parent is not None:
            if self in new_parent.children:
                raise RuntimeError('wtf, how???')
            new_parent.children.add(self)

    def remove(self):
        if self._parent is not None:
            self._parent.children.remove(self)

    def render(self, *args, **kwargs):
        pass

    def update(self):
        pass
