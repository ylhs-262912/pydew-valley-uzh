import pygame
from pytmx import TiledMap

from src import support
from src.enums import GameState
from src.gui.interface.dialog import DialogueManager

from src.gui.setup import setup_gui
from src.screens.level import Level
from src.screens.menu import MainMenu
from src.screens.pause import PauseMenu
from src.screens.settings import SettingsMenu
from src.screens.shop import ShopMenu
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, AniFrames, MapDict, SoundDict, EMOTE_SIZE


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.display_surface = pygame.display.set_mode(screen_size)
        pygame.display.set_caption('PyDew')

        # frames
        self.character_frames: dict[str, AniFrames] | None = None
        self.level_frames: dict | None = None
        self.tmx_maps: MapDict | None = None
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.frames: dict[str, dict] | None = None

        # assets
        self.tmx_maps: dict[str, TiledMap] | None = None

        self.emotes: AniFrames | None = None

        self.font: pygame.font.Font | None = None
        self.sounds: SoundDict | None = None

        # main setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.load_assets()

        # screens
        self.level = Level(self.switch_state, self.tmx_maps, self.frames, self.sounds)
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(self.switch_state, self.sounds, self.level)
        self.shop_menu = ShopMenu(self.level.player, self.switch_state, self.font)

        # dialog
        self.dm = DialogueManager(self.level.all_sprites)

        # screens
        self.menus = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.SHOP: self.shop_menu,
            GameState.LEVEL: self.level
        }
        self.current_state = GameState.MAIN_MENU

    def switch_state(self, state):
        self.current_state = state

    def load_assets(self):
        self.tmx_maps = support.tmx_importer('data/maps')

        # frames
        self.character_frames = support.character_importer('images/characters')

        self.emotes = support.animation_importer("images/ui/emotes/sprout_lands",
                                                 frame_size=EMOTE_SIZE, resize=EMOTE_SIZE)

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

        self.frames = {
            'character': self.character_frames,
            "emotes": self.emotes,
            'level': self.level_frames,
            'overlay': self.overlay_frames
        }

        setup_gui()

        # sounds
        self.sounds = support.sound_importer('audio', default_volume=0.25)

        self.font = support.import_font(30, 'font/LycheeSoda.ttf')

    def game_paused(self):
        return self.current_state != GameState.LEVEL

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000


            # removing level update because it makes two times for event in pygame.event.get() so it makes the game laggy
            # self.level.update(dt)

            # if self.game_paused():
            self.menus[self.current_state].update(dt)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
