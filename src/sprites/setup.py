import os
from dataclasses import dataclass

import pygame

from src.enums import Direction, EntityState
from src.settings import SCALE_FACTOR


@dataclass
class _AniFrames:
    frames: list[pygame.Surface]
    hitboxes: list[pygame.Rect] | pygame.Rect | None = None

    def get_frame(self, index: int) -> pygame.Surface:
        return self.frames[int(index % len(self.frames))]

    def get_hitbox(self, index: int) -> pygame.Rect:
        if isinstance(self.hitboxes, pygame.Rect):
            return self.hitboxes
        else:
            return self.hitboxes[int(index % len(self.frames))]

    def __len__(self) -> int:
        return len(self.frames)


@dataclass
class _EntityStateAsset:
    _data: dict[Direction, _AniFrames]

    def __getitem__(self, direction: Direction) -> _AniFrames:
        return self._data[direction]


@dataclass
class EntityAsset:
    _data: dict[EntityState, dict[Direction, _AniFrames]]

    def __getitem__(self, state: EntityState) -> dict[Direction, _AniFrames]:
        return self._data[state]


class EntityAssets:
    Rabbit: EntityAsset

    @classmethod
    def setup(cls):

        rabbit_hitboxes = {
            Direction.LEFT: pygame.Rect(20, 26, 8, 6),
            Direction.UP: pygame.Rect(18, 26, 12, 6),
            Direction.RIGHT: pygame.Rect(20, 26, 8, 6),
            Direction.DOWN: pygame.Rect(18, 26, 12, 6),
        }

        rabbit_asset = entity_importer(
            path="images/characters/rabbit",
            size=48,
            directions=[Direction.DOWN, Direction.UP, Direction.LEFT],
            hitboxes=rabbit_hitboxes
        )

        cls.Rabbit = EntityAsset(
            rabbit_asset
        )


_StateHitboxTypes = (
        dict[Direction, list[pygame.Rect] | pygame.Rect]
        | pygame.Rect
)


def state_importer(
        path: str, size: int, directions: list[Direction],
        hitboxes: _StateHitboxTypes
) -> dict[Direction, _AniFrames]:

    directions_dict = {}
    full_path = os.path.join(path)
    surf = pygame.image.load(full_path).convert_alpha()

    for row, direction in enumerate(directions):
        frames = []

        for col in range(surf.get_width() // size):
            cutout_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cutout_rect = pygame.Rect(
                col * size,
                row * size,
                size,
                size
            )

            cutout_surf.blit(surf, (0, 0), cutout_rect)
            frames.append(
                pygame.transform.scale_by(cutout_surf, SCALE_FACTOR))

        if isinstance(hitboxes, pygame.Rect):
            current_hitboxes = hitboxes
        else:
            current_hitboxes = hitboxes[direction]
        directions_dict[direction] = _AniFrames(
            frames, current_hitboxes
        )

    if Direction.LEFT in directions and Direction.RIGHT not in directions:
        frames = []
        hitboxes = []
        for i in range(len(directions_dict[Direction.LEFT])):
            frame = directions_dict[Direction.LEFT].get_frame(i)
            frame = pygame.transform.flip(frame, True, False)
            frames.append(frame)
            hitboxes.append(directions_dict[Direction.LEFT].get_hitbox(i))
        directions_dict[Direction.RIGHT] = _AniFrames(frames, hitboxes)
    elif Direction.RIGHT in directions and Direction.LEFT not in directions:
        directions_dict[Direction.LEFT] = [
            pygame.transform.flip(surf, True, False)
            for surf in directions_dict[Direction.RIGHT]
        ]
    return directions_dict


def scale_nested_rects(item: dict | list | pygame.Rect, factor: int):
    if isinstance(item, dict):
        for value in item.values():
            scale_nested_rects(value, factor)
    elif isinstance(item, list):
        for i in item:
            scale_nested_rects(i, factor)
    elif isinstance(item, pygame.Rect):
        item.update(
            item.left * factor,
            item.top * factor,
            item.width * factor,
            item.height * factor
        )


_EntityHitboxTypes = (
        dict[EntityState, dict[Direction, list[pygame.Rect] | pygame.Rect]]
        | dict[Direction, list[pygame.Rect] | pygame.Rect]
        | pygame.Rect
)


def entity_importer(
        path: str, size: int, directions: list[Direction],
        hitboxes: _EntityHitboxTypes
) -> dict[EntityState, dict[Direction, _AniFrames]]:
    scale_nested_rects(hitboxes, SCALE_FACTOR)
    states = {}
    for folder_path, sub_folders, file_names in os.walk(path):
        for file_name in file_names:
            current_state = EntityState(file_name.split(".")[0])
            if isinstance(hitboxes, pygame.Rect):
                states[current_state] = state_importer(
                    os.path.join(folder_path, file_name),
                    size=size,
                    directions=directions,
                    hitboxes=hitboxes,
                )
            else:
                states[current_state] = state_importer(
                    os.path.join(folder_path, file_name),
                    size=size,
                    directions=directions,
                    hitboxes=(hitboxes.get(current_state) or hitboxes),
                )
    return states
