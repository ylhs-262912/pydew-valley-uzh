import pygame

from src.gui.scene_animation import SceneAnimation
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.sprites.base import Sprite


class Camera:
    def __init__(self, width: int, height: int):
        self._width, self._height = width, height
        self.state = pygame.Rect(0, 0, width, height)

    def change_size(self, width: int, height: int):
        self._width, self._height = width, height
        self.state.size = width, height

    def update(self, target: Sprite | SceneAnimation):
        self.state.update(self._complex_camera(target.rect))

    def apply(self, target: Sprite):
        return target.rect.move(self.state.topleft)

    @property
    def size(self):
        return self._width, self._height

    def _complex_camera(self, target_rect: pygame.Rect):
        left, top = target_rect.topleft
        w, h = self.size
        left, top = (
            (SCREEN_WIDTH / 2) - left,
            (SCREEN_HEIGHT / 2) - top,
        )  # center player

        left = min(0, left)  # stop scrolling at the left edge
        left = max(-(w - SCREEN_WIDTH), left)  # stop scrolling at the right edge
        top = max(-(h - SCREEN_HEIGHT), top)  # stop scrolling at the bottom
        top = min(0, top)  # stop scrolling at the top

        return pygame.Rect(
            left - (target_rect.width / 2), top - (target_rect.height / 2), w, h
        )
