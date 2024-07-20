from abc import ABC, abstractmethod
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
        self.frame_index = 0
        self.state = EntityState.IDLE
        self.facing_direction = Direction.DOWN

        super().__init__(
            pos,
            self.assets[self.state][self.facing_direction].get_frame(0),
            groups,
            z=z
        )

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_sprites = collision_sprites

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

    def get_state(self):
        self.state = 'walk' if self.direction else 'idle'

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

    @abstractmethod
    def move(self, dt):
        pass

    # FIXME: Sometimes NPCs get stuck inside the player's hitbox
    def collision(self) -> bool:
        """
        :return: true: Entity collides with a sprite in self.collision_sprites, otherwise false
        """
        colliding_rect = None

        for sprite in self.collision_sprites:
            if sprite is not self:

                # Entities should collide with their hitbox_rects to make them able to approach
                #  each other further than the empty space on their sprite images would allow
                if isinstance(sprite, CollideableSprite):
                    if sprite.hitbox_rect.colliderect(self.hitbox_rect):
                        colliding_rect = sprite.hitbox_rect
                elif sprite.rect.colliderect(self.hitbox_rect):
                    colliding_rect = sprite.rect

                if colliding_rect:
                    distances = (
                        abs(self.hitbox_rect.right - colliding_rect.left),
                        abs(self.hitbox_rect.left - colliding_rect.right),
                        abs(self.hitbox_rect.bottom - colliding_rect.top),
                        abs(self.hitbox_rect.top - colliding_rect.bottom)
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

        return bool(colliding_rect)

    def animate(self, dt):
        current_animation = self.assets[self.state][self.facing_direction]

        self.frame_index += 4 * dt
        if not self.tool_active:
            self.image = current_animation.get_frame(self.frame_index)
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

    def update(self, dt):
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)

