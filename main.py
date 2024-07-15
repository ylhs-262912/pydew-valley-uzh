import sys

import pygame

from src import settings
from src import support
from src.enums import GameState
from src.npc.dialog import DialogueManager, prepare_tb_image
from src.screens.level import Level
from src.screens.menu_main import MainMenu
from src.screens.menu_pause import PauseMenu
from src.screens.menu_settings import SettingsMenu
from src.screens.shop import ShopMenu
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.display_surface = pygame.display.set_mode(screen_size)
        pygame.display.set_caption('PyDew')

        # frames
        self.character_frames: dict[str, settings.AniFrames] | None = None
        self.level_frames: dict | None = None
        self.tmx_maps: settings.MapDict | None = None
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.frames: dict[str, dict] | None = None

        # assets
        self.tmx_maps = {}
        self.sounds = None
        self.font = None
        self._tb_base = None
        self.tb_main_text_base_surf: pygame.Surface | None = None
        self.tb_cname_base_surf: pygame.Surface | None = None
        self.font: pygame.font.Font | None = None
        self.sounds: settings.SoundDict | None = None

        # main setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.load_assets()

        # screens
        self.level = Level(self, self.switch_state, self.tmx_maps, self.frames, self.sounds)
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(self.switch_state, self.sounds, self.level.player.controls)
        self.shop_menu = ShopMenu(self.level.player, self.switch_state, self.font)

        # dialog
        self.dm = DialogueManager(self.level.all_sprites, self.tb_cname_base_surf, self.tb_main_text_base_surf)

        # screens
        self.menus = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.SHOP: self.shop_menu,
            # GameState.LEVEL: self.level
        }
        self.current_state = GameState.MAIN_MENU

    def switch_state(self, state: GameState):
        self.current_state = state
        if self.game_paused():
            self.level.player.blocked = True
            self.level.player.direction.update((0, 0))
        else:
            self.level.player.blocked = False

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
        self.frames = {
            'character': self.character_frames,
            'level': self.level_frames,
            'overlay': self.overlay_frames
        }

        self._tb_base = pygame.image.load(support.resource_path("images/textbox.png")).convert_alpha()
        self.tb_cname_base_surf = self._tb_base.subsurface(pygame.Rect(0, 0, 212, 67))
        self.tb_main_text_base_surf = self._tb_base.subsurface(pygame.Rect(0, 74, 391, 202))
        prepare_tb_image(self.tb_cname_base_surf, self.tb_main_text_base_surf)

        # sounds
        self.sounds = support.sound_importer('audio', default_volume=0.25)

        self.font = support.import_font(30, 'font/LycheeSoda.ttf')

    def game_paused(self):
        return self.current_state != GameState.LEVEL

    # events
    def event_loop(self):
        for event in pygame.event.get():
            if self.handle_event(event):
                continue

            if self.game_paused():
                if self.menus[self.current_state].handle_event(event):
                    continue

            if self.level.handle_event(event):
                continue

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        return False

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            self.event_loop()

            self.level.update(dt)

            if self.game_paused():
                self.menus[self.current_state].update(dt)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
