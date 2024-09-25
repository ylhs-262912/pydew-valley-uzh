from collections.abc import Callable

import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons

from src.enums import GameState
from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import Button
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import import_image
import json

_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class GeneralMenu(AbstractMenu):
    def __init__(
        self,
        title: str,
        options: list[str],
        switch: Callable[[GameState], None],
        size: tuple[int, int],
        set_token_status: Callable[[bool], None],  # For token status update
        center: vector = None,
    ):
        if center is None:
            center = vector()

        super().__init__(title, size, center)

        self.options = options
        self.button_setup()

        # switch
        self.switch_screen = switch

        # textbox input
        self.input_active = False
        self.input_box = pygame.Rect(100, 390, 200, 50)  # Position and size of the textbox
        self.input_text = ''
        self.token_entered = False
        self.play_button_enabled = False

        # Callback to update token status in Game
        self.set_token_status = set_token_status

        # Load the UZH logo image
        self.logo_image = import_image("images/UZH logo/UZH logo.png")
        self.logo_image = pygame.transform.scale(self.logo_image, (216.5, 75))

    def draw_input_box(self):
        button_width = 400
        button_height = 50
        box_color = (255, 255, 255)
        border_color = (141, 133, 201)
        text_color = (0, 0, 0)
        background_color = (210, 204, 255)  # Purple background

        self.input_box.width = button_width
        self.input_box.height = button_height
        self.input_box.centerx = _SCREEN_CENTER[0]

        background_rect = self.input_box.copy()
        background_rect.inflate_ip(0, 50)
        background_rect.move_ip(0, -8)
        pygame.draw.rect(self.display_surface, background_color, background_rect, border_radius=10)

        if self.input_active:
            label_font = self.font
            label_text = "Please enter token:"
            label_surface = label_font.render(label_text, True, text_color)

            # Position the label slightly above the input box
            label_rect = label_surface.get_rect(midbottom=(self.input_box.centerx, self.input_box.top + 5))
            self.display_surface.blit(label_surface, label_rect)

        # Draw the input box
        pygame.draw.rect(self.display_surface, box_color, self.input_box, border_radius=10)
        pygame.draw.rect(self.display_surface, border_color, self.input_box, 3, border_radius=10)

        # Render the current text inside the input box
        font = self.font
        text_surface = font.render(self.input_text, True, text_color)
        text_rect = text_surface.get_rect(midleft=(self.input_box.x + 10, self.input_box.centery))
        self.display_surface.blit(text_surface, text_rect)

    def draw(self):
        self.draw_title()
        self.draw_buttons()
        self.UZH_logo()
        # Draw the input box if it's active
        if self.input_active:
            self.draw_input_box()

    def UZH_logo(self):
        # Semi-transparent background
        background_surface = pygame.Surface((300, 80), pygame.SRCALPHA)
        background_surface.fill((255, 255, 255, 128))
        background_rect = background_surface.get_rect(
            center=(SCREEN_WIDTH // 2, 129)
        )
        self.display_surface.blit(background_surface, background_rect)
        logo_rect = self.logo_image.get_rect(center=(SCREEN_WIDTH // 2, 129))
        self.display_surface.blit(self.logo_image, logo_rect)

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

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            self.pressed_button = self.get_hovered_button()
            if self.input_box.collidepoint(event.pos):
                self.input_active = True  # Activate the input box
            else:
                self.input_active = False  # Deactivate the input box if clicked outside
            if self.pressed_button:
                self.pressed_button.start_press_animation()
                return True

        if event.type == pygame.MOUSEBUTTONUP:
            if self.pressed_button:
                self.pressed_button.start_release_animation()
                if self.pressed_button.mouse_hover():
                    self.button_action(self.pressed_button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                self.pressed_button = None
                return True

        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    if self.validate_token(self.input_text):  # Check if the token is valid
                        self.play_button_enabled = True
                        self.save_token(self.input_text)
                        self.token_entered = self.input_text
                        self.set_token_status(True)
                        self.input_active = False
                        self.input_text = ''
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos) and self.input_active:
                self.input_active = True
            else:
                self.input_active = False
        return False

    def validate_token(self, token: str) -> bool:
        """Validate the entered token. Only '000' and '999' is valid."""
        valid_tokens = ["000","999"]
        return token in valid_tokens

    def save_token(self, token: str):
        """Save the token to a JSON file."""
        with open("token_data.json", "w") as file:
            json.dump({"token": token}, file)

    def button_action(self, text: str):
        if text == "Play":
            if self.play_button_enabled:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                self.switch_screen(GameState.PLAY)
        elif text == "Enter a Token to Play":
            self.input_active = True  # Activate the textbox for input
            self.token_entered = False  # Reset token entered flag
        if text == "Quit":
            self.quit_game()
