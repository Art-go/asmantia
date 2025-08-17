from __future__ import annotations

from dataclasses import dataclass
from math import floor, ceil, sqrt


# noinspection PyTypeHints
@dataclass
class Vec2:
    x: int | float = 0
    y: int | float = 0

    @property
    def tuple(self):
        return self.x, self.y

    @property
    def int_tuple(self):
        return int(self.x), int(self.y)

    @classmethod
    def from_tuple(cls, tpl: tuple):
        return cls(tpl[0], tpl[1])

    def __add__(self, other: Vec2 | tuple | (int | float)):
        if isinstance(other, Vec2):
            return Vec2(x=self.x + other.x, y=self.y + other.y)
        elif isinstance(other, tuple):
            return Vec2(x=self.x + other[0], y=self.y + other[1])
        elif isinstance(other, (int, float)):
            return Vec2(x=self.x + other, y=self.y + other)
        else:
            raise TypeError(f"Can't add {type(other)} to {type(self)}")

    def __sub__(self, other: Vec2 | tuple | (int | float)):
        if isinstance(other, Vec2):
            return Vec2(x=self.x - other.x, y=self.y - other.y)
        elif isinstance(other, tuple):
            return Vec2(x=self.x - other[0], y=self.y - other[1])
        elif isinstance(other, (int, float)):
            return Vec2(x=self.x - other, y=self.y - other)
        else:
            raise TypeError(f"Can't sub {type(other)} from {type(self)}")

    def __mul__(self, other: int | tuple | float | Vec2):
        if isinstance(other, Vec2):
            return Vec2(x=self.x * other.x, y=self.y * other.y)
        elif isinstance(other, tuple):
            return Vec2(x=self.x * other[0], y=self.y * other[1])
        elif isinstance(other, (int, float)):
            return Vec2(x=self.x * other, y=self.y * other)
        else:
            raise TypeError(f"Can't multiply {type(self)} by {type(other)}")

    def __truediv__(self, other: tuple | int | float | Vec2):
        if isinstance(other, Vec2):
            return Vec2(x=self.x / other.x, y=self.y / other.y)
        elif isinstance(other, tuple):
            return Vec2(x=self.x / other[0], y=self.y / other[1])
        elif isinstance(other, (int, float)):
            return Vec2(x=self.x / other, y=self.y / other)
        else:
            raise TypeError(f"Can't divide {type(self)} by {type(other)}")

    def __floordiv__(self, other: int | tuple | float | Vec2):
        if isinstance(other, Vec2):
            return Vec2(x=self.x // other.x, y=self.y // other.y)
        elif isinstance(other, tuple):
            return Vec2(x=self.x // other[0], y=self.y // other[1])
        elif isinstance(other, (int, float)):
            return Vec2(x=self.x // other, y=self.y // other)
        else:
            raise TypeError(f"Can't divide {type(self)} by {type(other)}")

    def __floor__(self):
        return Vec2(x=floor(self.x), y=floor(self.y))

    def __ceil__(self):
        return Vec2(x=ceil(self.x), y=ceil(self.y))

    def __round__(self):
        return Vec2(x=int(self.x), y=int(self.y))

    def __eq__(self, other: Vec2):
        return self.x == other.x and self.y == other.y

    def __gt__(self, other: Vec2):
        return self.x > other.x or self.y > other.y

    def __lt__(self, other: Vec2):
        return self.x < other.x or self.y < other.y

    def __ge__(self, other: Vec2):
        return self.x > other.x and self.y > other.y

    def __le__(self, other: Vec2):
        return self.x < other.x and self.y < other.y

    def __neg__(self):
        return Vec2(x=-self.x, y=-self.y)

    def __mod__(self, other: int):
        if isinstance(other, int):
            return Vec2(x=self.x % other, y=self.y % other)
        else:
            raise TypeError(f"Can't mod {type(self)} by {type(other)}")

    def normalize(self):
        len = self.len()
        return self / len if len > 0 else self.__class__()

    def len(self):
        return sqrt(self.x ** 2 + self.y ** 2)


zero = Vec2(0, 0)
one = Vec2(1, 1)
down = Vec2(0, 1)
up = Vec2(0, -1)
left = Vec2(-1, 0)
right = Vec2(1, 0)
