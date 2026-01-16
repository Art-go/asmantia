from dataclasses import dataclass
from typing import Optional

from Engine import Vec2


@dataclass(slots=True)
class Rect:
    pos: Vec2
    size: Vec2

    @property
    def end(self) -> Vec2:
        return self.pos + self.size

    @end.setter
    def end(self, new_end):
        self.size = new_end - self.pos

    def check_intersection(self, other: "Rect") -> bool:
        return other.pos < self.end and self.pos < other.end

    def get_intersection(self, other: "Rect") -> Optional["Rect"]:
        if not self.check_intersection(other):
            return None

        top_left = self.pos.max(other.pos)
        bottom_right = self.end.min(other.end)

        intersection_size = bottom_right - top_left
        return Rect(top_left, intersection_size)

    def __contains__(self, other: "Rect") -> bool:
        """Check if other Rect is completely inside this Rect"""
        return self.pos <= other.pos and self.end >= other.end

    def adjacent_to(self, other: "Rect") -> tuple[bool, bool, bool, bool]:
        """Check adjacency in order: top, bottom, left, right"""
        top = (self.pos.y == other.end.y and
               self.pos.x <= other.end.x and
               self.end.x >= other.pos.x)

        bottom = (self.end.y == other.pos.y and
                  self.pos.x <= other.end.x and
                  self.end.x >= other.pos.x)

        left = (self.pos.x == other.end.x and
                self.pos.y <= other.end.y and
                self.end.y >= other.pos.y)

        right = (self.end.x == other.pos.x and
                 self.pos.y <= other.end.y and
                 self.end.y >= other.pos.y)

        return top, bottom, left, right
