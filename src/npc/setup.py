import math
from contextlib import contextmanager

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.chicken_base import ChickenBase
from src.npc.bases.cow_base import CowBase
from src.npc.bases.npc_base import NPCBase
from src.settings import SCALED_TILE_SIZE
from src.sprites.entities.player import Player


class AIData:
    Matrix: list[list[int]] = None
    Grid: Grid = None

    player: Player = None

    _setup: bool = False

    @classmethod
    def update(cls, pathfinding_matrix: list[list[int]], player: Player) -> None:
        if not cls._setup:
            NPCBase.pf_finder = AStarFinder()
            ChickenBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )
            CowBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )

            cls._setup = True

        cls.Matrix = pathfinding_matrix
        cls.Grid = Grid(matrix=cls.Matrix)

        for ai in (NPCBase, ChickenBase, CowBase):
            ai.pf_matrix = cls.Matrix
            ai.pf_grid = cls.Grid

        cls.player = player


@contextmanager
def pf_grid_temporary_exclude(*positions: tuple[int, int]):
    _old_walkable_values: dict[tuple[int, int], bool] = {}

    try:
        for x, y in positions:
            _old_walkable_values[(x, y)] = AIData.Grid.walkable(x, y)
            AIData.Grid.node(x, y).walkable = False
        yield
    finally:
        for x, y in positions:
            AIData.Grid.node(x, y).walkable = _old_walkable_values[(x, y)]


@contextmanager
def pf_exclude_player_position():
    player_hitbox = AIData.player.hitbox_rect
    player_x_min = int(player_hitbox.left / SCALED_TILE_SIZE)
    player_x_max = math.ceil(player_hitbox.right / SCALED_TILE_SIZE)
    player_y_min = int(player_hitbox.top / SCALED_TILE_SIZE)
    player_y_max = math.ceil(player_hitbox.bottom / SCALED_TILE_SIZE)

    player_tile_positions = [
        (x + player_x_min, y + player_y_min)
        for x in range(player_x_max - player_x_min)
        for y in range(player_y_max - player_y_min)
    ]

    with pf_grid_temporary_exclude(*player_tile_positions) as ctx:
        yield ctx
