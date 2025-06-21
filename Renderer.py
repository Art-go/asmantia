import pygame

import Utils
from Object import Obj
from Vec2 import Vec2


class Renderer(Obj):
    img: pygame.Surface
    scaled_img: dict[int | float, pygame.Surface]
    size: Vec2

    def __init__(self, img: pygame.Surface, pos=None, *, parent=None, scalable=True):
        super().__init__(pos=pos, parent=parent)
        self.img = img.convert_alpha()
        self.scaled_img = {}
        self.size = Vec2.from_tuple(self.img.get_size())
        self.scalable = scalable
        if scalable:
            self.scale(1)

    def scale(self, factor: int | float):
        assert len(self.scaled_img) < 1024
        if not self.scalable:
            self.scaled_img[factor] = self.img
            return
        self.scaled_img[factor] = pygame.transform.scale(
            self.img, ((self.size * factor).__ceil__()).tuple)

    def render(self, cam):
        """

        :type cam: Camera.Camera
        """
        if cam.zoom not in self.scaled_img:
            self.scale(cam.zoom)
        rect = self.scaled_img[cam.zoom].get_rect(center=cam.world_to_screen(self.global_pos).tuple)
        cam.screen.blit(self.scaled_img[cam.zoom], rect)


class TextRenderer(Renderer):
    def __init__(self, text: str, font: pygame.font.Font, fore: tuple, back: tuple, pos=None,
                 *, parent=None, scalable=True):
        super().__init__(Utils.prerender_text(text, font, fore, back), pos, parent=parent, scalable=scalable)
