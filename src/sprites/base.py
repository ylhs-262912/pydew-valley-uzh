from abc import ABC

import pygame

from src.mapobjects import MapObjectType
from src.settings import LAYERS, SCALE_FACTOR


class Sprite(pygame.sprite.Sprite):
    def __init__(self,
                 pos: tuple[int | float,
                            int | float],
                 surf: pygame.Surface,
                 groups: tuple[pygame.sprite.Group] | pygame.sprite.Group,
                 z: int = LAYERS['main'],
                 name: str | None = None):
        super().__init__(groups)
        self.surf = surf
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.name = name


class CollideableSprite(Sprite, ABC):
    hitbox_rect: pygame.Rect


class CollideableMapObject(CollideableSprite):
    def __init__(
            self,
            pos: tuple[int, int],
            object_type: MapObjectType,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
            z=LAYERS['main']
    ):
        self.object_type = object_type

        surf = pygame.transform.scale_by(self.object_type.image, SCALE_FACTOR)

        super().__init__(pos, surf, groups, z)

        self.hitbox_rect = self.object_type.hitbox.move(self.rect.topleft)


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, frames[0], groups, z)

    def animate(self, dt):
        self.frame_index += 2 * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def update(self, dt):
        self.animate(dt)

