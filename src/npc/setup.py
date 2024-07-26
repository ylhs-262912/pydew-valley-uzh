from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.behaviour.cow_behaviour_tree import CowSharedContext
from src.sprites.character import Character


class AIData:
    Matrix: list[list[int]] = None
    Grid: Grid = None

    NPCPathFinder: AStarFinder = None
    ChickenPathFinder: AStarFinder = None
    CowPathFinder: AStarFinder = None

    @classmethod
    def setup(
            cls, pathfinding_matrix: list[list[int]], player: Character
    ) -> None:
        CowSharedContext.player = player

        cls.Matrix = pathfinding_matrix
        cls.Grid = Grid(matrix=cls.Matrix)

        cls.NPCPathFinder = AStarFinder()
        cls.ChickenPathFinder = AStarFinder(
            diagonal_movement=DiagonalMovement.only_when_no_obstacle
        )
        cls.CowPathFinder = AStarFinder(
            diagonal_movement=DiagonalMovement.only_when_no_obstacle
        )
