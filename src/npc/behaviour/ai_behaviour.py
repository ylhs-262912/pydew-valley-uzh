import random
from abc import ABC
from collections.abc import Callable

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.behaviour.ai_behaviour_base import AIBehaviourBase, AIState
from src.settings import SCALED_TILE_SIZE
from src.support import screen_to_tile


class AIBehaviour(AIBehaviourBase, ABC):
    def __init__(  # noqa
            self,
            pf_matrix: list[list[int]],
            pf_grid: Grid,
            pf_finder: AStarFinder
    ):
        """
        !IMPORTANT! AIBehaviour doesn't call Entity.__init__ while still
        relying on it. Be aware that when inheriting from AIBehaviour you
        should first inherit from Entity itself, or inherit from another class
        that has Entity as base.
        """
        self.pf_matrix = pf_matrix
        self.pf_grid = pf_grid
        self.pf_finder = pf_finder

        # AI-controlled Entities will idle for 1-4s on game start
        self.pf_state = AIState.IDLE
        self.pf_state_duration = random.random() * 3 + 1

        self.pf_path = []

        self.__on_path_abortion_funcs = []
        self.__on_path_completion_funcs = []

    def on_path_abortion(self, func: Callable[[], None]):
        self.__on_path_abortion_funcs.append(func)
        return

    def abort_path(self):
        self.pf_state = AIState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = 1

        for func in self.__on_path_abortion_funcs:
            func()

        self.__on_path_abortion_funcs.clear()
        self.__on_path_completion_funcs.clear()

        self.exit_moving()
        return

    def on_path_completion(self, func: Callable[[], None]):
        self.__on_path_completion_funcs.append(func)
        return

    def complete_path(self):
        self.pf_state = AIState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = random.randint(2, 5)

        for func in self.__on_path_completion_funcs:
            func()

        self.__on_path_abortion_funcs.clear()
        self.__on_path_completion_funcs.clear()

        self.exit_moving()
        return

    def exit_idle(self):
        pass

    def exit_moving(self):
        pass

    def create_path_to_tile(self, coord: tuple[int, int]) -> bool:
        """
        Initiates the AI-controlled Entity to move to the specified tile.
        :param coord: Coordinate of the tile the Entity should move to.
        :return: Whether the path has successfully been created.
        """

        if not self.pf_grid.walkable(coord[0], coord[1]):
            return False

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(
            self.rect.centerx, self.rect.centery
        ) / SCALED_TILE_SIZE

        self.pf_state = AIState.MOVING
        self.pf_state_duration = 0

        self.pf_grid.cleanup()

        try:
            start = self.pf_grid.node(int(tile_coord.x), int(tile_coord.y))
        except IndexError as e:
            # FIXME: Occurs when NPCs get stuck inside each other at the edge
            #  of the map and one of them gets pushed out of the walkable area
            print(f"NPC is at invalid location {tile_coord}\nFull error: {e}")
            return False
        end = self.pf_grid.node(*[int(i) for i in coord])

        path_raw = self.pf_finder.find_path(start, end, self.pf_grid)

        # The first position in the path will always be removed as it is the
        # same coordinate the NPC is already standing on. Otherwise, if the NPC
        # is just standing a little bit off the center of its current
        # coordinate, it may turn around quickly once it reaches it, if the
        # second coordinate of the path points in the same direction as where
        # the NPC was just standing.
        self.pf_path = [(i.x + .5, i.y + .5) for i in path_raw[0][1:]]

        if not self.pf_path:
            self.abort_path()
            return False

        return True

    def move(self, dt: float):
        self.hitbox_rect.update(
            (self.rect.x + self._current_hitbox.x,
             self.rect.y + self._current_hitbox.y),
            self._current_hitbox.size
        )

        if self.pf_state == AIState.IDLE:
            self.update_idle(dt)
        elif self.pf_state == AIState.MOVING:
            self.update_moving()

        super().move(dt)

        if self.is_colliding:
            self.abort_path()

    def update_idle(self, dt: float):
        self.pf_state_duration -= dt
        if self.pf_state_duration <= 0:
            self.exit_idle()

    def update_moving(self):
        if not self.pf_path:
            self.complete_path()
            return

        # Get the next point in the path
        next_point = self.pf_path[0]
        current_point = screen_to_tile(self.rect.center)

        # Calculate the direction vector
        dx = next_point[0] - current_point[0]
        dy = next_point[1] - current_point[1]

        # If the NPC is close enough to the next point, move to the next point
        if abs(dx) < 1 and abs(dy) < 1:
            self.next_path_point()

        # Normalize the direction vector
        magnitude = dx + dy
        if magnitude:
            self.direction.x = round(dx / magnitude)
            self.direction.y = round(dy / magnitude)
        else:
            self.direction.xy = (0, 0)

    def next_path_point(self):
        self.pf_path.pop(0)
        if not self.pf_path:
            # NPC has reached the end of the path
            self.direction.x, self.direction.y = 0, 0
            return
