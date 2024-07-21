from __future__ import annotations
from typing import Callable, Self

import pygame  # noqa

from src import settings, savefile, support
from src.controls import Controls, ControlType
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.settings import SCALE_FACTOR
from src.sprites.entity import Entity


_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Entity):
    def __init__(
            self,
            game,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups,
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[[FarmingTool, tuple[int, int], Entity], None],
            interact: Callable[[], None],
            sounds: settings.SoundDict,
            font: pygame.font.Font):

        save_data = savefile.load_savefile()
        self.game = game

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,
            (44 * SCALE_FACTOR, 40 * SCALE_FACTOR),
            apply_tool
        )

        # movement
        self.controls = Controls
        self.load_controls()
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact
        self.sounds = sounds

        # menus

        self.current_tool = save_data.get("current_tool", FarmingTool.get_first_tool_id())
        self.tool_index = self.current_tool.value - 1

        self.current_seed = save_data.get("current_seed", FarmingTool.get_first_seed_id())
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
            )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def save(self):
        # We compact the inventory first, i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(self.current_tool, self.current_seed, self.money, compacted_inv)

    def load_controls(self):
        self.controls.load_default_keybinds()
        try:
            data = support.load_data('keybinds.json')
            self.controls.from_dict(data)
        except FileNotFoundError:
            support.save_data(self.controls.as_dict(), 'keybinds.json')

    # controls
    def update_controls(self):
        keys_just_pressed = pygame.key.get_just_pressed()
        keys_pressed = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()

        for control in self.controls.all_controls():
            if control.control_type == ControlType.key:
                control.just_pressed = keys_just_pressed[control.value]
                control.pressed = keys_pressed[control.value]

            if control.control_type == ControlType.mouse:
                control.pressed = mouse_pressed[control.value]

    def handle_controls(self):
        self.update_controls()

        # movement
        if not self.tool_active and not self.blocked:
            self.direction.x = int(self.controls.RIGHT.pressed) - int(self.controls.LEFT.pressed)
            self.direction.y = int(self.controls.DOWN.pressed) - int(self.controls.UP.pressed)
            self.direction = self.direction.normalize() if self.direction else self.direction

            # tool switch
            if self.controls.NEXT_TOOL.just_pressed:
                self.tool_index = (self.tool_index + 1) % len(self.available_tools)
                self.current_tool = FarmingTool(self.tool_index + FarmingTool.get_first_tool_id())

            # tool use
            if self.controls.USE.just_pressed:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if self.controls.NEXT_SEED.just_pressed:
                self.seed_index = (self.seed_index + 1) % len(self.available_seeds)
                self.current_seed = FarmingTool(self.seed_index + FarmingTool.get_first_seed_id())

            # seed used
            if self.controls.PLANT.just_pressed:
                self.use_tool(ItemToUse.SEED)

            # interact
            if self.controls.INTERACT.just_pressed:
                self.interact()

    def move(self, dt: float):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center
        self.plant_collide_rect.center = self.hitbox_rect.center

    def get_current_tool_string(self):
        return self.available_tools[self.tool_index]

    def get_current_seed_string(self):
        return self.available_seeds[self.seed_index]

    def add_resource(self, resource: InventoryResource, amount: int = 1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update(self, dt):
        self.handle_controls()
        super().update(dt)
