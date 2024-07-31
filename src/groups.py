import pygame

from src.enums import Layer
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Coordinate


class PersistentSpriteGroup(pygame.sprite.Group):
    _persistent_sprites: list[pygame.sprite.Sprite]

    def __init__(self):
        super().__init__()
        self._persistent_sprites = []

    def add_persistent(self, *sprites: pygame.sprite.Sprite):
        super().add(*sprites)
        self._persistent_sprites.extend(sprites)

    def empty(self):
        super().empty()
        self.add(*self._persistent_sprites)

    def empty_persistent(self):
        super().empty()


# TODO : we could replace this with pygame.sprite.LayeredUpdates, as that
#  is a subclass of pygame.sprite.Group that natively supports layers


class AllSprites(PersistentSpriteGroup):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
        self.cam_surf = pygame.Surface(self.display_surface.get_size())

    def draw(self, target_pos: Coordinate):
        self.offset.x = -(target_pos[0] - SCREEN_WIDTH / 2)
        self.offset.y = -(target_pos[1] - SCREEN_HEIGHT / 2)

        sorted_sprites = sorted(self.sprites(),
                                key=lambda spr: spr.hitbox_rect.bottom)

        for layer in Layer:
            for sprite in sorted_sprites:
                if sprite.z == layer:
                    sprite.draw(self.display_surface, self.offset)
