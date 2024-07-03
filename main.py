from src.settings import *
from src.support import *
from src.level import Level
from src.main_menu import MainMenu, PauseMenu, SettingsMenu
from src.settings_menu import settings_menu


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyDew')
        
        # frames
        self.character_frames = None
        self.level_frames = None
        self.overlay_frames = None

        # assets
        self.tmx_maps = None
        self.sounds = None
        self.font = None
        self.load_assets()
        
        # game setup
        self.running = True
        self.clock = pygame.time.Clock()

        # screens
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        # self.settings_menu = settings_menu(self.font, self.sounds)
        self.settings_menu = SettingsMenu(self.switch_state)
        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds, self.switch_state)

        self.screens = {'menu': self.main_menu, 'level': self.level, 'pause': self.pause_menu, 'settings': self.settings_menu}
        self.current_state = 'menu'
    
    def switch_state(self, state):
        self.current_state = state

    def load_assets(self):
        self.tmx_maps = tmx_importer('data/maps')

        # frames
        self.level_frames = {
            'animations': animation_importer('images', 'animations'),
            'soil': import_folder_dict('images/soil'),
            'soil water': import_folder_dict('images/soil water'),
            'tomato': import_folder('images/plants/tomato'),
            'corn': import_folder('images/plants/corn'),
            'rain drops': import_folder('images/rain/drops'),
            'rain floor': import_folder('images/rain/floor'),
            'objects': import_folder_dict('images/objects')
        }
        self.overlay_frames = import_folder_dict('images/overlay')
        self.character_frames = character_importer('images/characters')

        self.sounds = sound_importer('audio', default_volume=0.25)

        self.font = import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            screen = self.screens[self.current_state]
            screen.update(dt)
            # self.menu_update()

            pygame.display.update()

        
    def menu_update(self):
        keys = pygame.key.get_just_pressed()
        
        if self.level.entities["Player"].paused:
            pause_menu = self.level.entities["Player"].pause_menu
            self.settings_menu = False

            if pause_menu.pressed_play:
                self.level.entities["Player"].paused = not self.level.entities["Player"].paused
                pause_menu.pressed_play = False

            elif pause_menu.pressed_quit:
                pause_menu.pressed_quit = False
                self.running = False
                self.main_menu.menu = True
                self.level.entities["Player"].paused = False
                self.main_menu.run()

            elif pause_menu.pressed_settings:
                self.settings_menu = self.level.entities["Player"].settings_menu

            if self.settings_menu and self.settings_menu.go_back:
                self.settings_menu.go_back = False
                self.settings_menu = False
                pause_menu.pressed_settings = False

            if not self.settings_menu:
                pause_menu.update()

            if self.settings_menu:
                self.settings_menu.update()

        if self.settings_menu:
            if keys[pygame.K_ESCAPE]:
                self.settings_menu = False
                pause_menu.pressed_settings = False




if __name__ == '__main__':
    game = Game()
    game.run()