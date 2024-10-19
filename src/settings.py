import pygame  # noqa
import pygame.freetype
import pytmx

from src.enums import Map
from src.import_checks import *  # noqa: F403

type Coordinate = tuple[int | float, int | float]
type SoundDict = dict[str, pygame.mixer.Sound]
type MapDict = dict[str, pytmx.TiledMap]
type AniFrames = dict[str, list[pygame.Surface]]
type GogglesStatus = bool | None
type NecklaceStatus = bool | None
type HatStatus = bool | None
type HornStatus = bool | None
type OutgroupSkinStatus = bool | None

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 16
CHAR_TILE_SIZE = 48
SCALE_FACTOR = 4
SCALED_TILE_SIZE = TILE_SIZE * SCALE_FACTOR

RANDOM_SEED = 123456789

GAME_MAP = Map.NEW_FARM

ENABLE_NPCS = True
TEST_ANIMALS = True

SETUP_PATHFINDING = any((ENABLE_NPCS, TEST_ANIMALS))

EMOTE_SIZE = 48

GROW_SPEED = {"corn": 1, "tomato": 0.7}

OVERLAY_POSITIONS = {
    "tool": (86, 150),
    "seed": (47, 142),
    "clock": (SCREEN_WIDTH - 10, 10),
    "FPS": (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10),
}

APPLE_POS = {
    "small": [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    "default": [(12, 12), (46, 10), (40, 34), (3, 42), (65, 55), (32, 59)],
    "bush": [(10, 10), (8, 37), (25, 25), (40, 13), (33, 40)],
}

CHARS_PER_LINE = 45
TB_SIZE = (493, 264)

HEALTH_DECAY_VALUE = 0.002
BATH_STATUS_TIMEOUT = 30

DEFAULT_ANIMATION_NAME = "intro"
