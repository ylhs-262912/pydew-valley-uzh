import pygame
from .settings import *


from .pause_menu import Button
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons

class GeneralMenu:
    def __init__(self, title, options, switch_screen, size, background=None):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT)) if background else None
        self.title = title

        # rect
        self.size = size
        self.rect = None
        self.rect_setup()

        # buttons
        self.options = options
        self.buttons = []
        self.button_setup()

        # switch
        self.switch_screen = switch_screen
    
    def rect_setup(self):
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def button_setup(self):
        button_width = 400
        button_height = 50
        space = 10
        generic_button_rect = pygame.Rect(self.rect.topleft, (button_width, button_height))
        for item in self.options:
            button = Button(item, self.font, generic_button_rect)
            self.buttons.append(button)
            generic_button_rect = generic_button_rect.move(0, button_height + space)

    def event_loop(self):
        self.mouse_hover()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.click(event)
            
    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.hover_active:
                    self.button_action(button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    
    def mouse_hover(self):
        for button in self.buttons:
            if button.hover_active:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                

    def button_action(self, text):
        if text == 'Play':
            self.switch_screen('level')
        if text == 'Quit':
            self.quit_game()
    
    def quit_game(self):
        pygame.quit()
        sys.exit()

    
    def draw_title(self):
        text_surf = self.font.render(self.title, False, 'Black')
        text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

        bg_rect = pygame.Rect((0, 0), (200, 50))
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def draw_background(self):
        if self.background:
            self.display_surface.blit(self.background, (0, 0))
    
    def draw_buttons(self):
        for button in self.buttons:
            button.draw()
    
    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
    
    def update(self, dt):
        self.event_loop()
        self.draw()



class MainMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Play', 'Quit']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Main Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)
    
    def button_action(self, text):
        if text == 'Play':
            self.switch_screen('level')
        if text == 'Quit':
            self.quit_game()


class PauseMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Resume', 'Options', 'Quit']
        title = 'Pause Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)
        
    def button_action(self, text):
        if text == 'Resume':
            self.switch_screen('level')
        if text == 'Options':
            self.switch_screen('settings')
        if text == 'Quit':
            self.switch_screen('menu')
        

class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Keybinds', 'Volume', 'Back']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Settings'
        size = (900, 400)
        super().__init__(title, options, switch_screen, size, background)

        self.slider = None
        self.import_data()
        self.adjust_rect()

        self.current_item = 0


    def button_action(self, text):
        if text == 'Keybinds':
            self.current_item = 0
        if text == 'Volume':
            self.current_item = 1
        if text == 'Back':
            self.switch_screen('menu')

    def import_data(self):
        self.options_data = { 
            0: {
                "Up": "UP ARROW",
                "Down": "DOWN ARROW",
                "Left": "LEFT ARROW",
                "Right": "RIGHT ARROW",
                "Use": "SPACE",
                "Cycle Tools": "Q",
                "Cycle Seeds": "E",
                "Plant Current Seed": "LCTRL",
            },
            1: {
             "slider": self.slider,
            },
        }


        
    def adjust_rect(self):
        width = 400 + 20 + 800
        height = 400
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        self.description_rect = pygame.Rect(0, 0, 600, 400)
        self.description_rect.topright = self.rect.topright
    
    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
        self.draw_description()
    
    def draw_keybinds(self):
        keys = ['Up', 'Down', 'Left', 'Right', 'Use', 'Cycle Tools', 'Cycle Seeds', 'Plant Current Seed']

    
    def draw_description(self):
        pygame.draw.rect(self.display_surface, 'White', self.description_rect, 0, 4)
        text = self.options_data[self.current_item]
        index = 0
        for key, value in text.items():
            text_surf = self.font.render(f'{key}: {value}', False, 'Black')
            text_rect = text_surf.get_frect(midtop=(self.description_rect.centerx, self.description_rect.top + 50 * index))
            self.display_surface.blit(text_surf, text_rect)
            index += 1

    

class KeySetup:
    def __init__(self):
        self.key_name = 'Up'
        self.key = pygame.K_UP
        self.symbol_image = None

        # rect
        self.rect = pygame.Rect(0, 0, 200, 50)
    
    def setup(self):
        pass

    def draw(self):
        pass
    

