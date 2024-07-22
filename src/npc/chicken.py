import pygame

from src.enums import LAYER
from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.chicken_behaviour_tree import (
    ChickenBehaviourTree,
    ChickenBehaviourTreeContext
)
from src.npc.setup import AIData
from src.settings import Coordinate, AniFrames


class Chicken(ChickenBase):
    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group
    ):
        super().__init__(
            pos=pos,
            frames=frames,
            groups=groups,
            collision_sprites=collision_sprites,

            pf_matrix=AIData.Matrix,
            pf_grid=AIData.Grid,
            pf_finder=AIData.ChickenPathFinder,

            z=LAYER.MAIN
        )

    def exit_idle(self):
        ChickenBehaviourTree.tree.run(ChickenBehaviourTreeContext(self))
