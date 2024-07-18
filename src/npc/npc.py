from typing import Callable, Self

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.enums import FarmingTool
from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import (
    NPCBehaviourTree,
    NPCBehaviourTreeContext
)
from src.overlay.soil import SoilLayer
from src.settings import Coordinate, AniFrames, LAYERS
from src.sprites.character import Character


class NPC(NPCBase):
    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[float, float], Self], None
            ],
            soil_layer: SoilLayer,
            pf_matrix: list[list[int]],
            pf_grid: Grid,
            pf_finder: AStarFinder
    ):
        self.soil_layer = soil_layer

        Character.__init__(
            self, pos, frames, groups, collision_sprites, apply_tool,
            z=LAYERS["main"]
        )
        AIBehaviour.__init__(self, pf_matrix, pf_grid, pf_finder)

    def exit_idle(self):
        NPCBehaviourTree.tree.run(NPCBehaviourTreeContext(self))
