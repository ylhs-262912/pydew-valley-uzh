import sys
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.support import resource_path
from src.gui.components import Button
from src.enums import GameState
from pygame.mouse import get_pressed as mouse_buttons
from pygame.math import Vector2 as vector
from abc import ABC

_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class AbstractMenu(ABC):
    pass
