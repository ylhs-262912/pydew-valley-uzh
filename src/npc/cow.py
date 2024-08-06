import pygame

from src.enums import Layer
from src.npc.bases.cow_base import CowBase
from src.npc.behaviour.cow_behaviour_tree import CowIndividualContext
from src.npc.setup import pf_exclude_player_position
from src.settings import Coordinate
from src.sprites.setup import EntityAsset
from src.support import get_sorted_flight_vectors


class Cow(CowBase):
    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            behaviour_tree_context=CowIndividualContext(self),
            z=Layer.MAIN,
        )

        self.fleeing = False

    def stop_moving(self):
        super().stop_moving()

        self.speed = 150
        self.fleeing = False

    def flee_from_pos(self, pos: tuple[int, int]) -> bool:
        """
        Aborts the current path of the cow and makes it flee into the opposite
        direction of the given position.
        :param pos: Position on the Tilemap that should be fled from
        """
        if not self.fleeing:
            self.abort_path()

            self.speed = 350
            self.fleeing = True

            # current NPC position on the tilemap
            tile_coord = self.get_tile_pos()

            with pf_exclude_player_position():
                flight_vectors = get_sorted_flight_vectors(
                    pos=(tile_coord[0] - pos[0], tile_coord[1] - pos[1]),
                    radius=5,
                )

                for coordinate in flight_vectors:
                    x_coord = tile_coord[0] + coordinate.x - 5
                    y_coord = tile_coord[1] + coordinate.y - 5
                    if self.pf_grid.walkable(x_coord, y_coord):
                        if self.create_path_to_tile((x_coord, y_coord)):
                            if len(self.pf_path) > 5:
                                self.pf_path = self.pf_path[:5]
                            return True
        return False
