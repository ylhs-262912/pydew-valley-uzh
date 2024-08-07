"""Implementation of a quake effect."""

from types import MappingProxyType

import pygame

from src.enums import Direction

_DIRECTIONAL_VECTORS = MappingProxyType(
    {
        Direction.UP: pygame.Vector2(0, -1),
        Direction.DOWN: pygame.Vector2(0, 1),
        Direction.LEFT: pygame.Vector2(-1, 0),
        Direction.RIGHT: pygame.Vector2(1, 0),
        Direction.UPLEFT: pygame.Vector2(-1, -1),
        Direction.UPRIGHT: pygame.Vector2(1, -1),
        Direction.DOWNLEFT: pygame.Vector2(-1, 1),
        Direction.DOWNRIGHT: pygame.Vector2(1, 1),
    }
)


class Quaker:
    def __init__(self):
        self.quaking = False
        self.quake_duration: float = 0
        self.quake_elapsed: float = 0
        self.direction: Direction | None = None
