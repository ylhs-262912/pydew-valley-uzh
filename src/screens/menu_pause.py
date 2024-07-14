import pygame

from src.enums import GameState
from src.gui.general_menu import GeneralMenu


class PauseMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Resume', 'Options', 'Quit']
        title = 'Pause Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text):
        if text == 'Resume':
            self.switch_screen(GameState.LEVEL)
        if text == 'Options':
            self.switch_screen(GameState.SETTINGS)
        if text == 'Quit':
            self.quit_game()

    def handle_event(self, event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.LEVEL)
                return True

        return False

