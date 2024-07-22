from abc import ABC
from typing import Callable
import pygame
from src import settings
from src.sprites.base import CollideableSprite, LAYERS
from src.enums import (
    InventoryResource, FarmingTool, ItemToUse, Direction, EntityState
)
from src.sprites.setup import EntityAsset
from src.support import screen_to_tile


class Entity(CollideableSprite, ABC):
    def __init__(
            self,
            pos: settings.Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            z=LAYERS['main']):

        self.assets = assets

        self._current_frame = None
        self._current_hitbox = None

        self._state = EntityState.IDLE
        self._facing_direction = Direction.DOWN
        self.frame_index = 0

        super().__init__(
            pos,
            self.assets[self.state][self.facing_direction].get_frame(0),
            groups,
            z=z,
        )

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_sprites = collision_sprites
        self.is_colliding = False

        self.last_hitbox_rect = self.hitbox_rect

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.current_tool = FarmingTool.get_first_tool_id()
        self.tool_index = self.current_tool.value - FarmingTool.get_first_tool_id().value

        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.available_seeds = ['corn', 'tomato']
        self.current_seed = FarmingTool.get_first_seed_id()
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 0,
            InventoryResource.TOMATO_SEED: 0,
        }

        # Not all Entities can go to the market, so those that can't should not have money either
        self.money = 0

    def update_frame(self):
        self._current_frame = self.assets[self.state][
            self.facing_direction
        ].get_frame(self.frame_index)

        self._current_hitbox = self.assets[self.state][
            self.facing_direction
        ].get_hitbox(self.frame_index)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: EntityState):
        self._state = state
        self.update_frame()

    @property
    def facing_direction(self):
        return self._facing_direction

    @facing_direction.setter
    def facing_direction(self, direction: Direction):
        self._facing_direction = direction
        self.update_frame()

    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, frame_index: int):
        self._frame_index = frame_index
        self.update_frame()

    def get_state(self):
        self.state = EntityState.WALK if self.direction else EntityState.IDLE

    def get_facing_direction(self):
        # prioritizes vertical animations, flip if statements to get horizontal
        # ones
        if self.direction.x:
            if self.direction.x > 0:
                self.facing_direction = Direction.RIGHT
            else:
                self.facing_direction = Direction.LEFT
        if self.direction.y:
            if self.direction.y > 0:
                self.facing_direction = Direction.DOWN
            else:
                self.facing_direction = Direction.UP

    def get_target_pos(self):
        return screen_to_tile(self.hitbox_rect.center)

    def move(self, dt):
        # x
        x_movement = self.direction.x * self.speed * dt
        self.rect.x += int(x_movement)

        # y
        y_movement = self.direction.y * self.speed * dt
        self.rect.y += int(y_movement)

        self.check_collision()

    # FIXME: Sometimes NPCs get stuck inside the player's hitbox
    def check_collision(self):
        """
        :return: true: Entity collides with a sprite in self.collision_sprites, otherwise false
        """
        colliding_rect = None

        for sprite in self.collision_sprites:
            if sprite is not self:

                if sprite.hitbox_rect.colliderect(self.hitbox_rect):
                    colliding_rect = sprite.hitbox_rect
                    distances_rect = colliding_rect

                    if isinstance(sprite, Entity):
                        # When colliding with another entity, the hitbox to
                        # compare to will also reflect its last-frame's state
                        distances_rect = sprite.last_hitbox_rect

                    # Compares each point of the last-frame's hitbox to the
                    # hitbox the Entity collided with, to check at which
                    # direction the collision happened first
                    distances = (
                        abs(self.last_hitbox_rect.right - distances_rect.left),
                        abs(self.last_hitbox_rect.left - distances_rect.right),
                        abs(self.last_hitbox_rect.bottom - distances_rect.top),
                        abs(self.last_hitbox_rect.top - distances_rect.bottom)
                    )

                    shortest_distance = min(distances)
                    if shortest_distance == distances[0]:
                        self.hitbox_rect.right = colliding_rect.left
                    elif shortest_distance == distances[1]:
                        self.hitbox_rect.left = colliding_rect.right
                    elif shortest_distance == distances[2]:
                        self.hitbox_rect.bottom = colliding_rect.top
                    elif shortest_distance == distances[3]:
                        self.hitbox_rect.top = colliding_rect.bottom

        self.is_colliding = bool(colliding_rect)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if not self.tool_active:
            self.image = self._current_frame
        else:
            tool_animation = self.assets[
                EntityState(self.available_tools[self.tool_index])
            ][self.facing_direction]
            if self.frame_index < len(tool_animation):
                self.image = tool_animation.get_frame(
                    min(round(self.frame_index), len(tool_animation) - 1)
                )
                if (round(self.frame_index) == len(tool_animation) - 1
                        and not self.just_used_tool):
                    self.just_used_tool = True
                    self.use_tool(ItemToUse.REGULAR_TOOL)
            else:
                # self.use_tool('tool')
                self.state = 'idle'
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option: ItemToUse):
        self.apply_tool((self.current_tool, self.current_seed)[option], self.get_target_pos(), self)

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount

    def prepare_for_update(self):
        # Updating all attributes necessary for updating the Entity
        self.last_hitbox_rect.update(self.hitbox_rect)
        self.get_state()
        self.get_facing_direction()

    def update(self, dt):
        self.prepare_for_update()
        self.move(dt)
        self.animate(dt)

