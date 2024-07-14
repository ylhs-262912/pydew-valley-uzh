import math

import pygame
import pygame.gfxdraw

from src.settings import EMOTE_LAYER, TB_LAYER, EMOTE_SIZE
from src.timer import Timer


def draw_aa_line(
        surface: pygame.Surface,
        center_pos: tuple[float, float],
        thickness: int,
        length: int,
        deg: float,
        color: tuple[int, int, int],
):
        ul = (center_pos[0] + (length / 2.) * math.cos(deg) - (thickness / 2.) * math.sin(deg),
              center_pos[1] + (thickness / 2.) * math.cos(deg) + (length / 2.) * math.sin(deg))
        ur = (center_pos[0] - (length / 2.) * math.cos(deg) - (thickness / 2.) * math.sin(deg),
              center_pos[1] + (thickness / 2.) * math.cos(deg) - (length / 2.) * math.sin(deg))
        bl = (center_pos[0] + (length / 2.) * math.cos(deg) + (thickness / 2.) * math.sin(deg),
              center_pos[1] - (thickness / 2.) * math.cos(deg) + (length / 2.) * math.sin(deg))
        br = (center_pos[0] - (length / 2.) * math.cos(deg) + (thickness / 2.) * math.sin(deg),
              center_pos[1] - (thickness / 2.) * math.cos(deg) - (length / 2.) * math.sin(deg))

        pygame.gfxdraw.aapolygon(surface, (ul, ur, br, bl), color)
        pygame.gfxdraw.filled_polygon(surface, (ul, ur, br, bl), color)


class EmoteBox(pygame.sprite.Sprite):
    z: int

    emote_dialog_box: pygame.Surface

    emote: list[pygame.Surface]
    _current_emote_image = pygame.Surface

    pos: tuple[float, float]

    _ani_frame_count: int
    _ani_cframe: int
    _ani_frame_length: float  # Time until a new frame of the animation plays in seconds
    _ani_length: float
    _ani_total_frames: int

    timer: Timer

    def __init__(
            self, pos: tuple[int, int],
            emote: list[pygame.Surface],
            emote_dialog_box: pygame.Surface
    ):
        super().__init__()
        self.z = EMOTE_LAYER

        self.emote_dialog_box = emote_dialog_box
        self.image = self.emote_dialog_box

        self.emote = emote
        self._current_emote_image = self.emote[0]

        self.rect = pygame.Rect(pos, self.emote_dialog_box.size)
        self.pos = self.rect.topleft

        self._ani_frame_count = len(self.emote)
        self._ani_cframe = -1
        self._ani_frame_length = self._ani_frame_count / 4
        self._ani_length = self._ani_frame_count * 2
        self._ani_total_frames = int(self._ani_length / self._ani_frame_length)

        # load first animation frame
        self._ani_next_frame()

        self.timer = Timer(self._ani_frame_length * 1000, repeat=True, autostart=False, func=self._ani_next_frame)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: tuple[float, float]):
        self._pos = value
        self.rect.update(self._pos, self.rect.size)

    def _ani_next_frame(self):
        self._ani_cframe += 1
        if self._ani_cframe >= self._ani_total_frames:
            # TODO: Remove reference from EmoteManager._emote_boxes
            self.kill()
            return

        self._current_emote_image = self.emote[self._ani_cframe % self._ani_frame_count]

        # update image
        self.image = self.emote_dialog_box.copy()
        self.image.blit(self._current_emote_image, (
            self.emote_dialog_box.width / 2 - self._current_emote_image.width / 2,
            self.emote_dialog_box.height / 2 - self._current_emote_image.height / 2 - 8,
        ))

    def update(self, *args, **kwargs):
        if not self.timer:
            self.timer.activate()
        self.timer.update()


class EmoteWheel(pygame.sprite.Sprite):
    def __init__(self, emote_manager: "EmoteManager"):
        super().__init__()
        self.z = TB_LAYER

        self.emote_manager = emote_manager

        # TODO: The emote wheel should be scaled down to not cover too much gameplay
        self.inner_radius = 48
        self.outer_radius = 128
        self.center = (self.outer_radius + self.inner_radius) / 2

        background_surface = pygame.Surface((self.outer_radius * 2, self.outer_radius * 2),
                                            flags=pygame.SRCALPHA)
        pygame.draw.circle(background_surface, (220, 185, 138), (self.outer_radius, self.outer_radius),
                           self.outer_radius - 2, int(self.outer_radius - self.inner_radius))
        background_surface.set_alpha(160)

        self._image = pygame.Surface((self.outer_radius * 2, self.outer_radius * 2),
                                     flags=pygame.SRCALPHA)
        self._image.blit(background_surface, (0, 0))

        self.emotes = ["cheer_ani", "cool_ani", "furious_ani", "love_ani",
                       "sad_ani", "sleep_ani", "smile_ani", "wink_ani"]
        self.emote_index = 0
        self.current_emote = self.emotes[self.emote_index]
        self._last_emote_index = None

        for i in range(len(self.emotes)):
            # draw lines as separators between the different emotes on the selector wheel
            deg = math.pi * 2 * i / len(self.emotes) - math.pi / 2

            # start_pos = (self.outer_radius + math.cos(deg) * self.inner_radius,
            #              self.outer_radius + math.sin(deg) * self.inner_radius)
            # end_pos = (self.outer_radius + math.cos(deg) * self.outer_radius,
            #            self.outer_radius + math.sin(deg) * self.outer_radius)

            # center_pos and length had to be slightly adjusted to be neither to short,
            #  nor to extend beyond the edge of the selector wheel
            center_pos = (self.outer_radius + math.cos(deg) * (self.center - 2),
                          self.outer_radius + math.sin(deg) * (self.center - 2))
            thickness = 4
            length = self.outer_radius - self.inner_radius - 2

            draw_aa_line(self._image, center_pos, thickness, length, deg, (170, 121, 89))

            # pygame.draw.line(self.emote_image, (170, 121, 89), start_pos, end_pos, thickness)

            # increase degree by half the distance to the next emote,
            #  to get the center of the current emote in the selector wheel
            deg = math.pi * 2 * (i + .5) / len(self.emotes) - math.pi / 2

            # blit first image of the emote as preview onto the selector wheel
            self._image.blit(self.emote_manager.emotes[self.emotes[i]][0],
                             (self.outer_radius - EMOTE_SIZE / 2 + math.cos(deg) * self.center,
                              self.outer_radius - EMOTE_SIZE / 2 + math.sin(deg) * self.center))

        # draw emote wheel outlines
        pygame.draw.aacircle(self._image, (170, 121, 89), (self.outer_radius, self.outer_radius),
                             self.inner_radius, 4)
        pygame.draw.aacircle(self._image, (170, 121, 89), (self.outer_radius, self.outer_radius),
                             self.outer_radius - 1, 4)

        self.image = self._image.copy()

        self.rect = pygame.Rect((0, 0), self.image.size)
        self.pos = self.rect.topleft

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self.rect.update((self._pos[0] - self.rect.width / 2,
                          self._pos[1] - self.rect.height / 2), self.rect.size)

    def update(self, *args, **kwargs):
        if self.image.get_alpha() == 0 or self._last_emote_index == self.emote_index:
            return

        self._last_emote_index = self.emote_index
        self.current_emote = self.emotes[self.emote_index % 8]

        self.image = self._image.copy()

        current_emote_index = self.emote_index % 8

        # draw thicker and brighter lines around the currently selected emote
        deg = math.pi * 2 * current_emote_index / 8 - math.pi / 2

        # center_pos and length had to be slightly adjusted to be neither to short,
        #  nor to extend beyond the edge of the selector wheel
        center_pos = (self.outer_radius + math.cos(deg) * (self.center - 3),
                      self.outer_radius + math.sin(deg) * (self.center - 3))
        thickness = 6
        length = self.outer_radius - self.inner_radius + 5

        draw_aa_line(
            self.image, center_pos, thickness, length, deg, (243, 229, 194)
        )

        deg = math.pi * 2 * (current_emote_index + 1) / 8 - math.pi / 2
        center_pos = (self.outer_radius + math.cos(deg) * (self.center - 3),
                      self.outer_radius + math.sin(deg) * (self.center - 3))

        draw_aa_line(
            self.image, center_pos, thickness, length, deg, (243, 229, 194)
        )

        start_deg = math.pi * 2 * -current_emote_index / 8 + math.pi / 4
        stop_deg = math.pi * 2 * (-current_emote_index + 1) / 8 + math.pi / 4

        pygame.draw.arc(self.image, (243, 229, 194), (0, 0,
                                                      self.outer_radius * 2,
                                                      self.outer_radius * 2), start_deg, stop_deg, 6)

        pygame.draw.arc(self.image, (243, 229, 194), (self.outer_radius - self.inner_radius - 1,
                                                      self.outer_radius - self.inner_radius - 1,
                                                      self.inner_radius * 2 + 2,
                                                      self.inner_radius * 2 + 2), start_deg, stop_deg, 6)


class EmoteManager:
    sprite_group: pygame.sprite.Group

    emotes: dict[str, list[pygame.Surface]]
    emote_dialog_box: pygame.Surface

    _emote_boxes: dict[int, EmoteBox]

    _show_emote_wheel: bool
    _emote_wheel: EmoteWheel

    def __init__(
            self, sprite_group: pygame.sprite.Group,
            emotes: dict[str, list[pygame.Surface]],
            emote_dialog_box: pygame.Surface
    ):
        self.sprite_group = sprite_group

        self.emotes = emotes
        self.emote_dialog_box = emote_dialog_box

        self._emote_boxes = {}

        self._show_emote_wheel = False
        self._emote_wheel = EmoteWheel(self)
        self._emote_wheel.image.set_alpha(0)
        self._emote_wheel.add(self.sprite_group)

    def update_emote_wheel(self, pos: tuple[int, int]):
        self._emote_wheel.pos = pos

    def toggle_emote_wheel(self, pos: tuple[int, int] = None):
        if pos is not None:
            self.update_emote_wheel(pos)

        # TODO: Figure out a way to truly hide the emote wheel so that it stops rendering every frame

        self._show_emote_wheel = not self._show_emote_wheel

        if self._show_emote_wheel:
            self._emote_wheel.image.set_alpha(255)
        else:
            self._emote_wheel.image.set_alpha(0)

    def _check_obj(self, obj: object):
        if id(obj) in self._emote_boxes.keys():
            return True
        return False

    def show_emote(self, obj: object, emote: str):
        if emote not in self.emotes.keys():
            raise KeyError(f"There is no Emote named \"{emote}\". Available emotes: {list(self.emotes.keys())}")

        if self._check_obj(obj):
            self._remove_emote_box(id(obj))

        self._emote_boxes[id(obj)] = EmoteBox((0, 0), self.emotes[emote], self.emote_dialog_box)
        self._emote_boxes[id(obj)].add(self.sprite_group)

    def update_obj(self, obj: object, pos: tuple[int, int]):
        if not self._check_obj(obj):
            return
        self._emote_boxes[id(obj)].pos = pos

    def _remove_emote_box(self, obj_id: int):
        self._emote_boxes[obj_id].kill()
        del self._emote_boxes[obj_id]

    def _clear_emote_boxes(self):
        for obj_id in self._emote_boxes.keys():
            self._remove_emote_box(obj_id)

    def __getitem__(self, obj: object):
        return self._emote_boxes[id(obj)]
