from abc import ABC, abstractmethod

import pygame

from src import settings
from src.enums import Direction, EntityState
from src.gui.interface import indicators
from src.settings import EMOTE_LAYER
from src.sprites.base import CollideableSprite, LAYERS, Sprite
from src.support import screen_to_tile, get_entity_facing_direction


class Entity(CollideableSprite, ABC):
    frames: dict[str, settings.AniFrames]
    frame_index: int
    _current_ani_frame: list[pygame.Surface] | None

    state: EntityState
    facing_direction: Direction

    direction: pygame.Vector2
    speed: int
    collision_sprites: pygame.sprite.Group
    plant_collide_rect: pygame.Rect

    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            shrink: tuple[int, int],
            z=LAYERS['main']):

        self.frames = frames
        self.frame_index = 0
        self._current_ani_frame = None
        self.state = EntityState.IDLE
        self.facing_direction = Direction.RIGHT

        self.focused = False
        self.focused_indicator = None

        super().__init__(
            pos,
            self.frames[self.state.value][
                self.facing_direction.value
            ][self.frame_index],
            groups,
            shrink,
            z=z
        )

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_sprites = collision_sprites
        self.plant_collide_rect = self.hitbox_rect.inflate(10, 10)

    def get_state(self):
        self.state = EntityState.WALK if self.direction else EntityState.IDLE

    def get_facing_direction(self):
        self.facing_direction = get_entity_facing_direction(
            self.direction, self.facing_direction
        )

    def get_target_pos(self):
        return screen_to_tile(self.hitbox_rect.center)

    def focus(self):
        self.focused = True
        self.focused_indicator = Sprite((0, 0), indicators.ENTITY_FOCUSED, self.groups()[0], EMOTE_LAYER)

    def unfocus(self):
        self.focused = False
        if self.focused_indicator:
            self.focused_indicator.kill()
            self.focused_indicator = None

    @abstractmethod
    def move(self, dt: float):
        pass

    # FIXME: Sometimes NPCs get stuck inside the player's hitbox
    def collision(self, direction: str) -> bool:
        """
        :return: true: Entity collides with a sprite in self.collision_sprites,
                 otherwise false
        """
        colliding_rect = False

        for sprite in self.collision_sprites:
            if sprite is not self:

                # Entities should collide with their hitbox_rects to make them
                # able to approach each other further than the empty space on
                # their sprite images would allow
                if isinstance(sprite, Entity):
                    if sprite.hitbox_rect.colliderect(self.hitbox_rect):
                        colliding_rect = sprite.hitbox_rect
                elif sprite.rect.colliderect(self.hitbox_rect):
                    colliding_rect = sprite.rect

                if colliding_rect:
                    if direction == 'horizontal':
                        if self.direction.x > 0:
                            self.hitbox_rect.right = colliding_rect.left
                        if self.direction.x < 0:
                            self.hitbox_rect.left = colliding_rect.right
                    else:
                        if self.direction.y < 0:
                            self.hitbox_rect.top = colliding_rect.bottom
                        if self.direction.y > 0:
                            self.hitbox_rect.bottom = colliding_rect.top

        return bool(colliding_rect)

    @abstractmethod
    def animate(self, dt: float):
        """
        Animate the Entity. Child classes should implement method and
        set current image based on self._current_ani_frame
        """
        self._current_ani_frame = self.frames[self.state.value][
            self.facing_direction
        ]
        self.frame_index += 4 * dt

    def update(self, dt: float):
        if self.focused_indicator:
            self.focused_indicator.rect.update((self.rect.centerx - self.focused_indicator.rect.width / 2,
                                                self.rect.centery - 56 - self.focused_indicator.rect.height / 2),
                                               self.focused_indicator.rect.size)
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)
