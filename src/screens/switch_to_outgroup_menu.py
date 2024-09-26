from collections.abc import Callable

import pygame

from src.enums import GameState, StudyGroup
from src.gui.menu.general_menu import GeneralMenu

# This menu is for when the player decides whether they will join the outgroup.


class OutgroupMenu(GeneralMenu):
    def __init__(self, player, switch_screen: Callable[[str], None]):
        options = ["Yes (Warning: You cannot go back after switching.)", "No"]
        title = "Would you like to join the outgroup?"
        size = (400, 400)
        self.player = player
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text):
        if "Yes" in text:
            self.player.study_group = StudyGroup.OUTGROUP
            self.player.has_hat = False
            self.player.has_necklace = False
            self.switch_screen(GameState.PLAY)
        elif "No" in text:
            self.switch_screen(GameState.PLAY)

    def outgroup_handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        return False
