from abc import ABC
from collections.abc import Callable
from typing import Self

import pygame

from src import settings
from src.enums import (
    FarmingTool, InventoryResource, ItemToUse, EntityState,
    LAYER
)
from src.settings import SCALE_FACTOR
from src.sprites.entity import Entity


class Character(Entity, ABC):
    current_tool: FarmingTool
    tool_active: bool
    just_used_tool: bool
    apply_tool: Callable[[FarmingTool, tuple[float, float], Self], None]

    current_seed: FarmingTool

    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[float, float], Self], None
            ],
            z=LAYER.MAIN
    ):
        Entity.__init__(
            self,
            pos=pos,
            frames=frames,
            groups=groups,
            collision_sprites=collision_sprites,

            shrink=(38 * SCALE_FACTOR, 40 * SCALE_FACTOR),

            z=z
        )

        # tools
        self.current_tool = FarmingTool(FarmingTool.get_first_tool_id())
        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.current_seed = FarmingTool(FarmingTool.get_first_seed_id())

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 0,
            InventoryResource.TOMATO_SEED: 0,
        }

        # Not all Characters can go to the market,
        # so those that can't should not have money either
        self.money = 0

    def animate(self, dt):
        super().animate(dt)
        if not self.tool_active:
            self.image = self._current_ani_frame[int(
                self.frame_index) % len(self._current_ani_frame)]
        else:
            tool_animation = self.frames[
                self.current_tool.as_serialised_string()
            ][self.facing_direction]
            if self.frame_index < len(tool_animation):
                self.image = tool_animation[min(
                    (round(self.frame_index), len(tool_animation) - 1))]
                if round(self.frame_index) == len(tool_animation) - \
                        1 and not self.just_used_tool:
                    self.just_used_tool = True
                    self.use_tool(ItemToUse.REGULAR_TOOL)
            else:
                self.state = EntityState.IDLE
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option: ItemToUse):
        self.apply_tool(
            (self.current_tool, self.current_seed)[option],
            self.get_target_pos(), self
        )

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount
