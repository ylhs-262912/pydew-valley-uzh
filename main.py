import sys
import pygame

from src import settings
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, GameState
from src import support
from src import level
from src import main_menu

from src.level import Level
from src.menus import MainMenu, PauseMenu, SettingsMenu, ShopMenu


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyDew')

        # frames
        self.character_frames: dict[str, settings.AniFrames] | None = None
        self.level_frames = None
        self.overlay_frames = None

        # assets
        self.tmx_maps = None
        self.sounds = None
        self.font = None
        self.level_frames: dict | None = None
        self.tmx_maps: settings.MapDict | None = None
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.font: pygame.font.Font | None = None
        self.sounds: settings.SoundDict | None = None
        pygame.init()
        self.screen = pygame.display.set_mode((
            settings.SCREEN_WIDTH,
            settings.SCREEN_HEIGHT,
        ))
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_assets()

        # game setup
        self.running = True
        self.level = level.Level(
            self.tmx_maps,
            self.character_frames,
            self.level_frames,
            self.overlay_frames,
            self.font,
            self.sounds)
        self.clock = pygame.time.Clock()

        # screens
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(self.switch_state, self.sounds)
        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds, self.switch_state)

        self.screens = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.LEVEL: self.level
        }

        self.current_state = GameState.MAIN_MENU

    def switch_state(self, state):
        self.current_state = state

    def load_assets(self):
        self.tmx_maps = support.tmx_importer('data/maps')

        # frames
        self.level_frames = {
            'animations': support.animation_importer('images', 'animations'),
            'soil': support.import_folder_dict('images/soil'),
            'soil water': support.import_folder_dict('images/soil water'),
            'tomato': support.import_folder('images/plants/tomato'),
            'corn': support.import_folder('images/plants/corn'),
            'rain drops': support.import_folder('images/rain/drops'),
            'rain floor': support.import_folder('images/rain/floor'),
            'objects': support.import_folder_dict('images/objects')
        }
        self.overlay_frames = support.import_folder_dict('images/overlay')
        self.character_frames = support.character_importer('images/characters')

        # sounds
        self.sounds = support.sound_importer('audio', default_volume=0.25)

        self.font = support.import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            screen = self.screens[self.current_state]
            screen.update(dt)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
