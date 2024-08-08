import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Type

import pygame
import pygame.gfxdraw
from pathfinding.core.grid import Grid

from src.controls import Controls
from src.enums import Direction
from src.groups import PersistentSpriteGroup
from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import AbstractButton
from src.npc.behaviour.cow_behaviour_tree import (
    CowConditionalBehaviourTree,
    CowContinuousBehaviourTree,
)
from src.npc.cow import Cow
from src.npc.setup import AIData
from src.overlay.overlay import Overlay
from src.screens.game_map import GameMap
from src.screens.minigames.base import Minigame, MinigameState
from src.settings import SCALE_FACTOR, SCREEN_HEIGHT, SCREEN_WIDTH, SoundDict
from src.sprites.base import Sprite
from src.sprites.entities.player import Player
from src.sprites.setup import ENTITY_ASSETS
from src.support import add_pf_matrix_collision, get_outline, import_font

# Colors taken from the Sprout Lands color palette
SL_BRIGHT = (243, 231, 216)
SL_MEDIUM = (220, 185, 138)
SL_DARKISH = (208, 169, 126)
SL_DARK = (170, 121, 89)
SL_DARKER = (135, 95, 69)


class _Button(AbstractButton):
    def __init__(self):
        super().__init__("Return to Town", pygame.Rect())
        self.font_button = import_font(28, "font/LycheeSoda.ttf")
        self.content = self.font_button.render(self._content, True, SL_BRIGHT)
        self._content_rect = self.content.get_frect()
        self.rect = self._content_rect.copy()

        # padding
        self.rect.width += 24
        self.rect.height += 12

        self.initial_rect = self.rect.copy()
        self._content_rect.center = self.rect.center

    @property
    def text(self):
        return self._content

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, SL_DARK, self.rect, 4, 4)
            self.color = SL_DARKISH
        else:
            self.hover_active = False
            pygame.draw.rect(self.display_surface, SL_DARK, self.rect, 4, 4)
            self.color = SL_MEDIUM

    def move(self, topleft: tuple[float, float]):
        self.rect.topleft = topleft
        self.initial_rect.topleft = topleft
        self._content_rect.center = self.rect.center

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, SL_DARKER, self.rect.move(3, 3), 6, 4)
        super().draw(surface)


class _CowHerdingScoreboard(AbstractMenu):
    def __init__(self, return_func: Callable[[], None]):
        super().__init__(title="Cow Herding", size=(SCREEN_WIDTH, SCREEN_HEIGHT))

        self._return_func = return_func
        self.return_button: _Button | None = None

        self._surface = pygame.Surface((0, 0))

        self.font_title = import_font(48, "font/LycheeSoda.ttf")
        self.font_number = import_font(36, "font/LycheeSoda.ttf")
        self.font_description = import_font(24, "font/LycheeSoda.ttf")
        self.font_button = import_font(32, "font/LycheeSoda.ttf")

    def setup(self, time_needed, cows_herded):
        box_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        padding = 12

        rendered_texts = [
            self.font_title.render("Success!", True, (243, 231, 216)),
            self.font_number.render(f"{time_needed:.2f}", True, (243, 231, 216)),
            self.font_description.render("seconds needed", True, (243, 231, 216)),
            self.font_number.render(f"{cows_herded}", True, (243, 231, 216)),
            self.font_description.render("cows herded", True, (243, 231, 216)),
        ]
        max_width = max([x.get_width() for x in rendered_texts])
        max_width = 256
        max_height = max([x.get_height() for x in rendered_texts])
        total_height = max_height * 5

        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))

        pygame.draw.rect(
            self._surface,
            SL_DARKER,
            (
                box_pos[0] - max_width / 2 - padding - 8 - 3,
                box_pos[1] - total_height / 2 - padding - 8 + 3,
                max_width + padding * 2 + 16 + 6,
                total_height + padding * 2 + 16,
            ),
            width=6,
            border_radius=16,
        )
        pygame.draw.rect(
            self._surface,
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
            self._surface,
            (220, 185, 138),
            (
                box_pos[0] - max_width / 2 - padding,
                box_pos[1] - total_height / 2 - padding,
                max_width + padding * 2,
                total_height + padding * 2,
            ),
            border_radius=8,
        )

        offset_y = total_height / 2

        self._surface.blit(
            rendered_texts[0],
            (
                box_pos[0] - rendered_texts[0].width / 2,
                box_pos[1] - offset_y,
            ),
        )

        offset_y = offset_y - (1 * max_height) - 12

        self._surface.blit(
            rendered_texts[1],
            (
                box_pos[0] - max_width / 2,
                box_pos[1] - offset_y,
            ),
        )

        self._surface.blit(
            rendered_texts[2],
            (
                box_pos[0] - max_width / 2 + rendered_texts[1].width + 6,
                box_pos[1] - offset_y + 9,
            ),
        )

        offset_y = offset_y - (1 * max_height)

        self._surface.blit(
            rendered_texts[3],
            (
                box_pos[0] - max_width / 2,
                box_pos[1] - offset_y,
            ),
        )

        self._surface.blit(
            rendered_texts[4],
            (
                box_pos[0] - max_width / 2 + rendered_texts[1].width + 6,
                box_pos[1] - offset_y + 9,
            ),
        )

        self.button_setup()
        self.return_button.move(
            (
                box_pos[0] - self.return_button.rect.width / 2,
                box_pos[1] - (total_height / 2 - (4 * max_height)),
            )
        )

    def button_action(self, name: str):
        if name == "Return to Town":
            self._return_func()

    def button_setup(self):
        self.return_button = _Button()
        self.buttons.append(self.return_button)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            self.pressed_button = self.get_hovered_button()
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

        return False

    def draw_buttons(self):
        for button in self.buttons:
            button.draw(self.display_surface)

    def draw(self):
        self.display_surface.blit(self._surface, (0, 0))
        self.draw_buttons()

    def update(self, dt):
        self.mouse_hover()

        self.update_buttons(dt)


class _CowHerdingOverlay:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font_countdown = import_font(128, "font/LycheeSoda.ttf")
        self.font_description = import_font(32, "font/LycheeSoda.ttf")
        self.font_objective = import_font(24, "font/LycheeSoda.ttf")
        self.font_timer = import_font(48, "font/LycheeSoda.ttf")

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
            SL_DARKER,
            (
                box_pos[0] - max_width / 2 - padding - 8 - 3,
                box_pos[1] - total_height / 2 - padding - 8 + 3,
                max_width + padding * 2 + 16 + 6,
                total_height + padding * 2 + 16,
            ),
            width=6,
            border_radius=16,
        )
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

    def render_objective(self, cows_total: int, cows_herded: int):
        objective_pos = (SCREEN_WIDTH, 0)
        padding = 12

        text = (
            "Objective:\n"
            "Herd the cows into the barn!\n"
            "\n"
            f"{cows_herded}/{cows_total} Cows in the barn"
        )
        rendered_texts = []
        for line in text.split("\n"):
            rendered_line = self.font_objective.render(line, True, (243, 231, 216))
            rendered_texts.append(rendered_line)
        max_width = max([x.get_width() for x in rendered_texts])
        max_height = max([x.get_height() for x in rendered_texts])
        total_height = sum([x.get_height() for x in rendered_texts])

        pygame.draw.rect(
            self.display_surface,
            SL_DARKER,
            (
                objective_pos[0] - max_width - padding * 2 - 8 - 3,
                objective_pos[1] - 3,
                max_width + padding * 2 + 8 + 6,
                total_height + padding * 2 + 8 + 6,
            ),
            width=6,
            border_bottom_left_radius=16,
        )
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
            SL_DARKER,
            (
                SCREEN_WIDTH / 2 - total_length / 2 - padding - 8 - 3,
                0 - 3,
                total_length + 16 + padding * 2 + 6,
                self.timer_char_height + padding / 2 + 8 + 6,
            ),
            width=6,
            border_bottom_left_radius=16,
            border_bottom_right_radius=16,
        )
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
    all_sprites: PersistentSpriteGroup
    collision_sprites: PersistentSpriteGroup
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
        self.scoreboard = _CowHerdingScoreboard(self.finish)

        self._ani_countdown_start = 5

        self._cows = []
        self._cows_original_positions = []
        self._cows_total = 0
        self._cows_herded = 0

        self._minigame_time = 0
        self._finished = False

        self._setup()

    @property
    def _finished(self):
        return self.__finished

    @_finished.setter
    def _finished(self, value: bool):
        if value:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))
            self.scoreboard.setup(self._minigame_time, self._cows_herded)
        else:
            self._state.player.blocked = False

        self.__finished = value

    def _setup(self):
        self.player_collision_sprites = self._state.collision_sprites.copy()

        self.l_barn_collider = None

        self.l_barn_matrix = [row.copy() for row in AIData.Matrix]

        colliders = {}
        cows = []
        for i in self._state.game_map.minigame_layer:
            if i.name == "Cow":
                pass
            elif i.name == "L_COW":
                cows.append(i)
            else:
                colliders[i.name] = i

        obj = colliders["LEFT_RANGE"]
        add_pf_matrix_collision(
            self.l_barn_matrix, (obj.x, obj.y), (obj.width, obj.height)
        )

        obj = colliders["LEFT_BARN_ENTRANCE"]
        pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        l_barn_entrance_collider = Sprite(pos, image, name=obj.name)
        add_pf_matrix_collision(
            self.l_barn_matrix, (obj.x, obj.y), (obj.width, obj.height)
        )
        l_barn_entrance_collider.add(self.player_collision_sprites)

        obj = colliders["LEFT_BARN_AREA"]
        pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        self.l_barn_collider = Sprite(pos, image, name=obj.name)

        self.l_barn_grid = Grid(matrix=self.l_barn_matrix)

        for obj in cows:
            pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
            cow = Cow(
                pos=pos,
                assets=ENTITY_ASSETS.COW,
                groups=(self._state.all_sprites, self._state.collision_sprites),
                collision_sprites=self._state.collision_sprites,
            )
            cow.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
            self._cows.append(cow)
            self._cows_original_positions.append(pos)

        self._cows_total = len(self._cows)

    def start(self):
        super().start()

        _set_player_controls(self.player_controls, True)
        self._state.player.facing_direction = Direction.UP
        self._state.player.blocked = True
        self._state.player.direction.update((0, 0))
        self._state.player.collision_sprites = self.player_collision_sprites

        self._state.overlay.visible = False

    def finish(self):
        super().finish()
        _set_player_controls(self.player_controls, False)
        self._state.player.blocked = False
        self._state.overlay.visible = True
        self._state.player.collision_sprites = self._state.collision_sprites

    def check_cows(self):
        cows_herded = []
        for cow in self._cows:
            if cow.hitbox_rect.colliderect(self.l_barn_collider.rect):
                cow.continuous_behaviour_tree = None
                cow.pf_grid = self.l_barn_grid
                cows_herded.append(cow)

        for cow in cows_herded:
            self._cows.remove(cow)
            self._cows_herded += 1

    def handle_event(self, event: pygame.Event):
        if self._finished:
            return self.scoreboard.handle_event(event)
        else:
            return False

    def update(self, dt: float):
        super().update(dt)

        if not self._finished:
            self._minigame_time = self._ctime - (self._ani_countdown_start + 3)

            if (self._ani_countdown_start + 3) < self._ctime:
                self.check_cows()
                if self._cows_total == self._cows_herded:
                    self._finished = True
        else:
            self.scoreboard.update(dt)

        # FIXME: Since map transitions / menus also access player.blocked, this is to
        #  make sure that the player remains blocked during the entire cutscene
        if self._ctime < self._ani_countdown_start + 3:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))

        if int(self._ctime - dt) != int(self._ctime):
            # Countdown starts, preparing minigame
            if int(self._ctime) == self._ani_countdown_start:
                for i in range(len(self._cows)):
                    self._cows[i].teleport(self._cows_original_positions[i])
                    self._cows[i].conditional_behaviour_tree = None
                    self._cows[i].abort_path()

            # Countdown counting
            if int(self._ctime) in [self._ani_countdown_start + i for i in range(3)]:
                self._state.sounds["countdown_count"].play()

            # Countdown finished, minigame starts
            elif int(self._ctime) == self._ani_countdown_start + 3:
                self._state.player.blocked = False
                self._state.sounds["countdown_end"].play()
                for cow in self._cows:
                    cow.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
                    cow.continuous_behaviour_tree = CowContinuousBehaviourTree.Flee

    def draw(self):
        if self._ctime <= self._ani_countdown_start:
            self.overlay.render_description()
        else:
            self.overlay.render_objective(self._cows_total, self._cows_herded)

        if self._ani_countdown_start < self._ctime < self._ani_countdown_start + 4:
            self.overlay.render_countdown(self._minigame_time)

        self.overlay.render_timer(self._minigame_time)

        if self._finished:
            self.scoreboard.draw()


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
