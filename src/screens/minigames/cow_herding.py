import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Type

import pygame
import pygame.gfxdraw

from src.controls import Controls
from src.enums import Direction
from src.overlay.overlay import Overlay
from src.screens.game_map import GameMap
from src.screens.minigames.base import Minigame, MinigameState
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, SoundDict
from src.sprites.entities.player import Player
from src.support import get_outline, import_font


class _CowHerdingOverlay:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font_countdown = import_font(128, "font/LycheeSoda.ttf")
        self.font_description = import_font(32, "font/LycheeSoda.ttf")
        self.font_objective = import_font(24, "font/LycheeSoda.ttf")
        self.font_timer = import_font(48, "font/LycheeSoda.ttf")  # "font/Noto_Sans/NotoSans-MediumItalic.ttf")

        self.timer_rendered_chars = {
            char: self.font_timer.render(char, True, (243, 231, 216))
            for char in "0123456789.:"
        }
        self.timer_char_width = max(
            char.width for char in self.timer_rendered_chars.values()
        )
        self.timer_char_height = max(
            char.height for char in self.timer_rendered_chars.values()
        )

    def render_countdown(self, current_time: float):
        """
        Displays ceil(abs(current_time)) if current_time < 0, else "GO!"
        """
        current_time_int = math.floor(current_time)
        current_fraction = abs(current_time) - abs(int(current_time))

        if current_time_int < 0:
            text = f"{abs(current_time_int)}"
            rendered_text = self.font_countdown.render(text, False, (231, 231, 231))

            if current_fraction >= 0.75:
                rendered_text = pygame.transform.scale_by(
                    rendered_text, (1 - current_fraction) * 4.5
                )
        else:
            text = "GO!"
            rendered_text = self.font_countdown.render(text, False, (255, 255, 255))
            if current_fraction <= 1 / 6:
                rendered_text = pygame.transform.scale_by(
                    rendered_text,
                    math.sin(current_fraction * 2 * math.pi * 4.5 + 0.5 * math.pi) / 8
                    + 1,
                )

        self.display_surface.blit(
            get_outline(rendered_text, (191, 191, 191), resize=True),
            (
                SCREEN_WIDTH / 2 - rendered_text.width / 2,
                SCREEN_HEIGHT / 3 - rendered_text.height / 2,
            ),
        )

    def render_description(self):
        box_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        padding = 12

        text = (
            "Mini-Game: Cow Herding\n"
            "\n"
            "Herd the cows into the barn\n"
            "as fast as possible!"
        )
        rendered_texts = []
        for line in text.split("\n"):
            rendered_line = self.font_description.render(line, True, (243, 231, 216))
            rendered_texts.append(rendered_line)
        max_width = max([x.get_width() for x in rendered_texts])
        max_height = max([x.get_height() for x in rendered_texts])
        total_height = sum([x.get_height() for x in rendered_texts])

        pygame.draw.rect(
            self.display_surface,
            (170, 121, 89),
            (
                box_pos[0] - max_width / 2 - padding - 8,
                box_pos[1] - total_height / 2 - padding - 8,
                max_width + padding * 2 + 16,
                total_height + padding * 2 + 16,
            ),
            border_radius=16,
        )
        pygame.draw.rect(
            self.display_surface,
            (220, 185, 138),
            (
                box_pos[0] - max_width / 2 - padding,
                box_pos[1] - total_height / 2 - padding,
                max_width + padding * 2,
                total_height + padding * 2,
            ),
            border_radius=8,
        )

        for pos, line in enumerate(rendered_texts):
            self.display_surface.blit(
                line,
                (
                    box_pos[0] - max_width / 2,
                    box_pos[1] - (total_height / 2 - (pos * max_height)),
                ),
            )

    def render_objective(self):
        objective_pos = (SCREEN_WIDTH, 0)
        padding = 12

        text = "Objective:\nHerd the cows into the barn!\n\n0/2 Cows in the barn"
        rendered_texts = []
        for line in text.split("\n"):
            rendered_line = self.font_objective.render(line, True, (243, 231, 216))
            rendered_texts.append(rendered_line)
        max_width = max([x.get_width() for x in rendered_texts])
        max_height = max([x.get_height() for x in rendered_texts])
        total_height = sum([x.get_height() for x in rendered_texts])

        pygame.draw.rect(
            self.display_surface,
            (170, 121, 89),
            (
                objective_pos[0] - max_width - padding * 2 - 8,
                objective_pos[1],
                max_width + padding * 2 + 8,
                total_height + padding * 2 + 8,
            ),
            border_bottom_left_radius=16,
        )
        pygame.draw.rect(
            self.display_surface,
            (220, 185, 138),
            (
                objective_pos[0] - max_width - padding * 2,
                objective_pos[1],
                max_width + padding * 2,
                total_height + padding * 2,
            ),
            border_bottom_left_radius=8,
        )

        for pos, line in enumerate(rendered_texts):
            self.display_surface.blit(
                line,
                (
                    objective_pos[0] - padding - max_width,
                    objective_pos[1] + padding + (pos * max_height),
                ),
            )

    def render_timer(self, current_time: float):
        t = max(0.0, current_time)
        timer_string = (
            f"{int(t / 60):02}"
            + ":"
            + f"{(int(t) - int(t / 60) * 60):02}"
            + "."
            + f"{t - int(t):.2f}"[2:]
        )

        total_length = 0

        for i in range(len(timer_string)):
            if timer_string[i].isdigit():
                total_length += self.timer_char_width
            else:
                total_length += self.timer_rendered_chars[timer_string[i]].width

        padding = 8

        pygame.draw.rect(
            self.display_surface,
            (170, 121, 89),
            (
                SCREEN_WIDTH / 2 - total_length / 2 - padding - 8,
                0,
                total_length + 16 + padding * 2,
                self.timer_char_height + padding / 2 + 8,
            ),
            border_bottom_left_radius=16,
            border_bottom_right_radius=16,
        )
        pygame.draw.rect(
            self.display_surface,
            (220, 185, 138),
            (
                SCREEN_WIDTH / 2 - total_length / 2 - padding,
                0,
                total_length + padding * 2,
                self.timer_char_height + padding / 2,
            ),
            border_bottom_left_radius=8,
            border_bottom_right_radius=8,
        )

        current_length = 0

        offset_y = 3

        for i in range(len(timer_string)):
            self.display_surface.blit(
                self.timer_rendered_chars[timer_string[i]],
                (SCREEN_WIDTH / 2 - total_length / 2 + current_length, offset_y),
            )
            if timer_string[i].isdigit():
                current_length += self.timer_char_width
            else:
                current_length += self.timer_rendered_chars[timer_string[i]].width


@dataclass
class CowHerdingState(MinigameState):
    player: Player
    game_map: GameMap
    overlay: Overlay
    get_camera_center: Callable[[], pygame.Vector2 | tuple[float, float]]
    sounds: SoundDict


class CowHerding(Minigame):
    _state: CowHerdingState
    player_controls: Type[Controls]

    def __init__(self, state: CowHerdingState):
        super().__init__(state)

        self.player_controls = self._state.player.controls

        self.display_surface = pygame.display.get_surface()
        self.font_countdown = import_font(128, "font/LycheeSoda.ttf")

        self.overlay = _CowHerdingOverlay()

        self._ani_countdown_start = 5

    def start(self):
        super().start()

        _set_player_controls(self.player_controls, True)
        self._state.player.facing_direction = Direction.UP
        self._state.player.blocked = True
        self._state.player.direction.update((0, 0))

        self._state.overlay.visible = False

    def finish(self):
        super().finish()
        _set_player_controls(self.player_controls, False)
        self._state.player.blocked = False
        self._state.overlay.visible = True

    def update(self, dt: float):
        super().update(dt)

        if self._ctime - dt < (self._ani_countdown_start + 3) < self._ctime:
            self._state.player.blocked = False

        if self._ani_countdown_start < self._ctime < self._ani_countdown_start + 4:
            if int(self._ctime) != self._ani_countdown_start + 3:
                if int(self._ctime - dt) != int(self._ctime):
                    self._state.sounds["countdown_count"].play()
            else:
                if int(self._ctime - dt) != int(self._ctime):
                    self._state.sounds["countdown_end"].play()

    def draw(self):
        if self._ctime <= self._ani_countdown_start:
            self.overlay.render_description()
        else:
            self.overlay.render_objective()

        if self._ani_countdown_start < self._ctime < self._ani_countdown_start + 4:
            self.overlay.render_countdown(self._ctime - self._ani_countdown_start - 3)

        self.overlay.render_timer(self._ctime - (self._ani_countdown_start + 3))


def _set_player_controls(controls: Type[Controls], value: bool):
    # movement is not disabled
    controls.USE.disabled = value
    controls.NEXT_TOOL.disabled = value
    controls.NEXT_SEED.disabled = value
    controls.PLANT.disabled = value
    # interact is not disabled
    controls.INVENTORY.disabled = value
    controls.EMOTE_WHEEL.disabled = value
    # overlays are not disabled
    controls.SHOW_DIALOG.disabled = value
    controls.ADVANCE_DIALOG.disabled = value
