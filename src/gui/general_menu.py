
import sys
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.support import resource_path
from src.gui.components import Button
from src.enums import GameState
from pygame.mouse import get_pressed as mouse_buttons
from pygame.math import Vector2 as vector
from src.gui.abstract_menu import AbstractMenu


_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class GeneralMenu(AbstractMenu):
    def __init__(self,  title, options, switch, size, center=vector()):
        super().__init__(title, size, center)

        self.options = options
        self.button_setup()

        # switch
        self.switch_screen = switch

    def button_setup(self):
        # button setup
        button_width = 400
        button_height = 50
        size = (button_width, button_height)
        space = 10
        top_margin = 20

        # generic button rect
        generic_button_rect = pygame.Rect((0, 0), size)
        generic_button_rect.top = self.rect.top + top_margin
        generic_button_rect.centerx = self.rect.centerx

        # create buttons
        for title in self.options:
            rect = generic_button_rect
            button = Button(title, rect, self.font)
            self.buttons.append(button)
            generic_button_rect = rect.move(0, button_height + space)

    def button_action(self, text):
        if text == 'Play':
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()
