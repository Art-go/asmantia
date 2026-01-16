from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from .rect import Rect
from .vec2 import Vec2


# WARNING: THIS CODE WAS WRITTEN BY DEEPSEEK AND ONLY MODIFIED BY ME SLIGHTLY. VIBECODE AHEAD
# I AM JUST TRUSTING IT TO HAVE IMPLEMENTED IT ALL CORRECTLY
# UPD: at this point, no, not really

class Packer(ABC):
    """Abstract base class for texture packing algorithms"""

    def __init__(self, atlas_size: Vec2):
        self.atlas_size = atlas_size
        self._init_packer()

    @abstractmethod
    def _init_packer(self) -> None:
        """Initialize the packer's internal data structures"""
        pass

    @abstractmethod
    def add_used_rect(self, rect: Rect) -> None:
        pass

    @abstractmethod
    def pack(self, size: Vec2) -> Optional[Vec2]:
        """
        Pack a new rectangle and return its position.
        Returns None if no space available.
        """
        pass

    def reset(self) -> None:
        self._init_packer()


class GuillotinePacker(Packer):
    """
    Guillotine packing algorithm.
    Splits free rectangles into two when placing a texture.
    Good for dynamic/streaming texture packing.
    """
    free_rects: list[Rect]

    def _init_packer(self) -> None:
        # Start with entire atlas as free
        self.free_rects: list[Rect] = [
            Rect(Vec2(0, 0), self.atlas_size.copy())
        ]

    def add_used_rect(self, rect: Rect) -> None:
        """Remove free rectangles that overlap with the used rectangle"""
        new_free_rects = []

        for free_rect in self.free_rects:
            self._split_free_rect(free_rect, rect, new_free_rects)

        self.free_rects = new_free_rects
        self._merge_free_rects()

    @staticmethod
    def _split_free_rect(free_rect: Rect, used_rect: Rect,
                         output: list[Rect]) -> None:
        """Split free rectangle around used rectangle, results are appended to output"""
        intersection = free_rect.get_intersection(used_rect)

        if intersection is None:
            output.append(free_rect)
            return

        # Generate new free rectangles
        # Left
        if intersection.pos.x > free_rect.pos.x:
            output.append(Rect(
                free_rect.pos,
                Vec2(intersection.pos.x - free_rect.pos.x, free_rect.size.y)
            ))

        # Right
        if intersection.end.x < free_rect.end.x:
            output.append(Rect(
                Vec2(intersection.end.x, free_rect.pos.y),
                Vec2(free_rect.end.x - intersection.end.x, free_rect.size.y)
            ))

        # Top
        if intersection.pos.y > free_rect.pos.y:
            output.append(Rect(
                Vec2(free_rect.pos.x, free_rect.pos.y),
                Vec2(free_rect.size.x, intersection.pos.y - free_rect.pos.y)
            ))

        # Bottom
        if intersection.end.y < free_rect.end.y:
            output.append(Rect(
                Vec2(free_rect.pos.x, intersection.end.y),
                Vec2(free_rect.size.x, free_rect.end.y - intersection.end.y)
            ))

    def _merge_free_rects(self) -> None:
        """Merge adjacent free rectangles to reduce fragmentation"""
        i = 0
        while i < len(self.free_rects) - 1:
            rect1 = self.free_rects[i]
            j = i + 1
            while j < len(self.free_rects):
                rect2 = self.free_rects[j]

                if rect2 in rect1:
                    self.free_rects.pop(j)
                    continue
                elif rect1 in rect2:
                    self.free_rects.pop(i)
                    i -= 1
                    break

                top, bottom, left, right = rect1.adjacent_to(rect2)

                if bottom and rect1.size.vy == rect2.size.vy:
                    self.free_rects[i] = Rect(rect1.pos, rect1.size + rect2.size.vy)
                elif top and rect1.size.vy == rect2.size.vy:
                    self.free_rects[i] = Rect(rect2.pos, rect2.size + rect1.size.vy)
                elif right and rect1.size.vx == rect2.size.vx:
                    self.free_rects[i] = Rect(rect1.pos, rect1.size + rect2.size.vx)
                elif left and rect1.size.vx == rect2.size.vx:
                    self.free_rects[i] = Rect(rect2.pos, rect2.size + rect1.size.vx)
                else:
                    j += 1
                    continue

                self.free_rects.pop(j)
                j = i + 1
            i += 1

    def _find_best_fit(self, size: Vec2) -> Optional[Rect]:
        """Find the best free rectangle to place the given size using best area fit heuristic"""
        best_rect = None
        best_score = float('inf')

        for free_rect in self.free_rects:
            # Use Vec2 >= operator to check if free rectangle can contain the size
            if free_rect.size >= size:
                # Calculate waste (remaining area)
                waste = (free_rect.size.x * free_rect.size.y) - (size.x * size.y)

                if waste < best_score:
                    best_score = waste
                    best_rect = free_rect

        return best_rect

    def pack(self, size: Vec2) -> Optional[Vec2]:
        """Pack a rectangle using best area fit heuristic"""
        best_rect = self._find_best_fit(size)
        if best_rect is None:
            return None
        position = best_rect.pos.copy()

        self.add_used_rect(Rect(position, size))

        return position


class SkylinePacker(Packer):
    r"""
    Note: this one is optimized for fixed height, so for analogy to hold, imagine city on a wall
    UPD: i am probably wrong about it, but i am halfway through rewriting it so... yeah ¯\_(ツ)_/¯
    """

    @dataclass(slots=True)
    class Segment:
        y: int
        height: int
        width: int
        @property
        def end(self) -> int:
            return self.y + self.height

    skyline: list[Segment]

    def _init_packer(self) -> None:
        # Skyline is stored as list of (y, height, width) tuples
        # Each entry represents a vertical segment at y=height from x to x+width
        self.skyline: list[SkylinePacker.Segment] = [self.Segment(0, self.atlas_size.y, 0)]
        self.used_rects: list[Rect] = []

    def add_used_rect(self, rect: Rect) -> None:
        self.used_rects.append(rect)
        self._update_skyline(rect)

    def _update_skyline(self, rect: Rect) -> None:
        """Update skyline with a new rectangle"""
        y_start = int(rect.pos.y)
        y_end = int(rect.end.y)
        width_new = int(rect.end.x)

        new_skyline: list[SkylinePacker.Segment] = []

        # Subdivide affected segments and move affected parts
        for seg in self.skyline:

            if seg.end <= y_start or seg.y >= y_end:
                # No overlap, skip
                new_skyline.append(seg)
                continue

            # Overlap
            # Part before rectangle
            if seg.y < y_start:
                new_skyline.append(self.Segment(seg.y, y_start - seg.y, seg.width))

            # Overlapping part - raise to rectangle's top if higher
            overlap_start = max(seg.y, y_start)
            overlap_end = min(seg.end, y_end)
            overlap_width = overlap_end - overlap_start
            new_skyline.append(self.Segment(overlap_start, overlap_width, max(seg.width, width_new)))

            # Part after rectangle
            if seg.end > y_end:
                new_skyline.append(self.Segment(y_end, seg.end - y_end, seg.width))

        # Merge segments w/ same height
        merged_skyline: list[SkylinePacker.Segment] = [new_skyline.pop(0)]
        for seg in new_skyline:
            prev = merged_skyline[-1]
            if prev.width == seg.width:
                assert prev.end == seg.y
                merged_skyline[-1].height = prev.height + seg.height
            else:
                merged_skyline.append(seg)

        self.skyline = merged_skyline

    def _find_best_fit(self, size: Vec2) -> Optional[Vec2]:
        """Find the best position to place the rectangle using bottom-left heuristic"""
        best_pos = None
        best_waste = float('inf')

        for i, seg in enumerate(self.skyline):
            potential_pos = Vec2(seg.width, seg.y)
            if potential_pos + size <= self.atlas_size:
                # There isn't a way to fit it in this segment
                continue
            if seg.height >= size.y:
                waste = self._calculate_waste(seg, size.y)
                if waste < best_waste:
                    best_waste = waste
                    best_pos = potential_pos
                continue

            # Try to fit by combining segments
            if i < len(self.skyline) - 1:
                combined_height = seg.height
                max_seg_width = seg.width
                j = i + 1

                while j < len(self.skyline) and combined_height < size.y:
                    seg2 = self.skyline[j]
                    max_seg_width = max(max_seg_width, seg2.width)
                    combined_height += seg2.height
                    j += 1

                potential_pos = Vec2(max_seg_width, seg.y)
                if combined_height >= size.y and potential_pos + size <= self.atlas_size:
                    waste = self._calculate_waste_for_combined(i, j, max_seg_width, size.y, combined_height)
                    if waste < best_waste:
                        best_waste = waste
                        best_pos = potential_pos

        return best_pos

    def pack(self, size: Vec2) -> Optional[Vec2]:
        """Pack a rectangle using bottom-left heuristic"""
        position = self._find_best_fit(size)
        if position is None:
            return None

        self.add_used_rect(Rect(position, size))
        return position

    @staticmethod
    def _calculate_waste(segment: Segment, height) -> int:
        return segment.height - height + segment.width * 16

    def _calculate_waste_for_combined(self, start_idx: int, end_idx: int,
                                      x: int, height: int, total_height: int) -> int:
        """Calculate waste for placing rectangle across multiple segments"""
        height_waste = total_height - height
        area_waste = 0

        for i in range(start_idx, end_idx - 1):
            seg = self.skyline[i]
            area_waste += (x - seg.width) * seg.height
        seg = self.skyline[end_idx - 1]
        area_waste += (x - seg.width) * (seg.height - height_waste)

        return area_waste + height_waste + x
