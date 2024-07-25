from __future__ import annotations

from typing import Callable

import pygame

from src.enums import FarmingTool, InventoryResource
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import (
    NPCBehaviourTree,
    NPCBehaviourTreeContext
)
from src.npc.setup import AIData
from src.overlay.soil import SoilLayer
from src.settings import (
    Coordinate, AniFrames, LAYERS
)
from src.sprites.character import Character


class NPC(NPCBase):
    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[int, int], Character], None
            ],
            plant_collision: Callable[
                [Character], None
            ],
            soil_layer: SoilLayer,
            emote_manager: NPCEmoteManager
    ):
        self.soil_layer = soil_layer

        self.emote_manager = emote_manager

        super().__init__(
            pos=pos,
            frames=frames,
            groups=groups,
            collision_sprites=collision_sprites,

            apply_tool=apply_tool,
            plant_collision=plant_collision,

            pf_matrix=AIData.Matrix,
            pf_grid=AIData.Grid,
            pf_finder=AIData.NPCPathFinder,

            z=LAYERS["main"]
        )

        # TODO: Ensure that the NPC always has all needed seeds it needs
        #  in its inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
        }

    def exit_idle(self):
        NPCBehaviourTree.tree.run(NPCBehaviourTreeContext(self))

    def update(self, dt):
        super().update(dt)

        self.emote_manager.update_obj(self, (self.rect.centerx - 47, self.rect.centery - 128))
