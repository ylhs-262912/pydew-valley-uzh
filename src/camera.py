import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.sprites.base import Sprite


class Camera:

    def __init__(self, width: int, height: int):
        self._width, self._height = width, height
        self.state = pygame.Rect(0, 0, width, height)

    def change_size(self, width:int, height: int):
        self._width, self._height = width, height
        self.state.size = width, height

    def update(self, target: Sprite):
        self.state.update(self._complex_camera(target.rect))

    def apply(self, target: Sprite):
        return target.rect.move(self.state.topleft)

    @property
    def size(self):
        return self._width, self._height

    def _complex_camera(self, target_rect):
        l, t = target_rect.topleft
        w, h = self.size
        l, t = (SCREEN_WIDTH / 2) - l, (SCREEN_HEIGHT / 2) - t  # center player

        l = min(0, l)  # stop scrolling at the left edge
        l = max(-(w - SCREEN_WIDTH), l)  # stop scrolling at the right edge
        t = max(-(h - SCREEN_HEIGHT), t)  # stop scrolling at the bottom
        t = min(0, t)  # stop scrolling at the top

        return pygame.Rect(l - (target_rect.width/2), t - (target_rect.height/2), w, h)
