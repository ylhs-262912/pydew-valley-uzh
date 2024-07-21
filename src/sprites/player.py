from __future__ import annotations

from typing import Callable, Self

import pygame

from src import settings, savefile, support
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.settings import AniFrames, Coordinate, SoundDict
from src.sprites.character import Character

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Character):
    keybinds: dict
    controls: dict

    blocked: bool
    paused: bool
    font: pygame.font.Font
    interact: Callable[[], None]
    sounds: SoundDict

    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[float, float], Self], None
            ],
            interact: Callable[[], None],
            sounds: SoundDict,
            font: pygame.font.Font
    ):
        save_data = savefile.load_savefile()

        super().__init__(
            pos=pos,
            frames=frames,
            groups=groups,
            collision_sprites=collision_sprites,
            apply_tool=apply_tool
        )

        # movement
        self.keybinds = self.import_controls()
        self.controls = {}
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact

        # load saved tools
        self.current_tool = save_data.get(
            "current_tool", FarmingTool.get_first_tool_id()
        )
        self.current_seed = save_data.get(
            "current_seed", FarmingTool.get_first_seed_id()
        )

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT
                if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
            )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def save(self):
        # We compact the inventory first,
        # i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(
            self.current_tool, self.current_seed, self.money, compacted_inv
        )

    @staticmethod
    def import_controls():
        try:
            data = support.load_data('keybinds.json')
            if len(data) == len(settings.KEYBINDS):
                return data
        except FileNotFoundError:
            pass
        support.save_data(settings.KEYBINDS, 'keybinds.json')
        return settings.KEYBINDS

    # controls
    def update_controls(self):
        controls = {}
        keys = pygame.key.get_just_pressed()
        linear_keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        for control_name, control in self.keybinds.items():
            control_type = control['type']
            value = control['value']
            if control_type == 'key':
                controls[control_name] = keys[value]
            if control_type == 'mouse':
                controls[control_name] = mouse_buttons[value]
            if control_name in ('up', 'down', 'left', 'right'):
                controls[control_name] = linear_keys[value]
        return controls

    def input(self):
        self.controls = self.update_controls()

        # movement
        if not self.tool_active and not self.blocked:
            self.direction.x = (int(self.controls['right'])
                                - int(self.controls['left']))
            self.direction.y = (int(self.controls['down'])
                                - int(self.controls['up']))
            if self.direction:
                self.direction = self.direction.normalize()

            # tool switch
            if self.controls['next tool']:
                tool_index = (
                        (self.current_tool.value
                         - FarmingTool.get_first_tool_id().value + 1)
                        % FarmingTool.get_tool_count()
                )
                self.current_tool = FarmingTool(
                    tool_index + FarmingTool.get_first_tool_id()
                )

            # tool use
            if self.controls['use']:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.math.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if self.controls['next seed']:
                seed_index = (
                        (self.current_seed.value
                         - FarmingTool.get_first_seed_id().value + 1)
                        % FarmingTool.get_seed_count()
                )
                self.current_seed = FarmingTool(
                    seed_index + FarmingTool.get_first_seed_id()
                )

            # seed used
            if self.controls['plant']:
                self.use_tool(ItemToUse.SEED)

            # interact
            if self.controls['interact']:
                self.interact()

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center
        self.plant_collide_rect.center = self.hitbox_rect.center

    def get_current_tool_string(self):
        return self.current_tool.as_serialised_string()

    def get_current_seed_string(self):
        return self.current_seed.as_serialised_string()

    def add_resource(self, resource, amount=1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update_keybinds(self):
        self.keybinds = self.import_controls()

    def update(self, dt):
        self.input()
        super().update(dt)
