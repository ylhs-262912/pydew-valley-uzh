import pygame
from .settings import *

from pygame import Vector2 as vector
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
    

    # setup
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


    # events
    def event_loop(self):
        self.mouse_hover()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
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


    # draw
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
    

    # update
    def update(self, dt):
        self.event_loop()
        self.draw()


# ------- Sub Menu Classes ------- #

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
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Pause Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        if text == 'Resume':
            self.switch_screen('level')
        if text == 'Options':
            self.switch_screen('settings')
        if text == 'Quit':
            self.quit_game()
        
class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen, sounds):
        options = ['Keybinds', 'Volume', 'Back']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Settings'
        size = (900, 400)
        super().__init__(title, options, switch_screen, size, background)

        # rect
        self.rect = None
        self.description_rect = None
        self.description_slider_surface = None
        self.adjust_rect()

        # slider
        topleft = self.description_rect.topleft + vector(50, 50)
        slider_rect = pygame.Rect(topleft, (200, 10))
        self.slider = Slider(slider_rect, 0, 100, 50, sounds)
        self.import_data()


        self.keys_group = []
        self.create_keybinds()

        self.description = self.draw_keybinds

    # setup
    def button_action(self, text):
        if text == 'Keybinds':
            self.description = self.draw_keybinds
        if text == 'Volume':
            self.description = self.draw_slider
        if text == 'Back':
            self.switch_screen('pause')

    def import_data(self):
        self.options_data = { 
            0: {
                "Up": "images/keys/up.svg",
                "Down": "images/keys/down.svg",
                "Left": "images/keys/left.png",
                "Right": "images/keys/right.svg",
                "Use": "images/keys/space.svg",
                "Cycle Tools": "images/keys/generic.svg",
                "Cycle Seeds": "images/keys/generic.svg",
                "Plant Current Seed": "images/keys/lctrl.png",
            },
            1: {
             "slider": self.slider,
            },
        }
        
    def adjust_rect(self):
        # main rect
        width = 400 + 20 + 800
        height = 400
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        # description
        self.description_rect = pygame.Rect(0, 0, 600, 400)
        self.description_rect.topright = self.rect.topright
        self.description_surface = pygame.Surface(self.description_rect.size)
        self.description_surface.set_colorkey('green')

        # slider
        self.description_slider_surface = pygame.Surface((600, 500))
        self.description_slider_rect = self.description_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')


    # events
    def event_loop(self):
        self.mouse_hover()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.click(event)
            self.mouse_wheel(event)
            self.slider.handle_event(event)
    
    def mouse_wheel(self, event):
        if event.type == pygame.MOUSEWHEEL:
            speed = 10
            self.description_slider_rect.y += event.y * speed
            self.description_slider_rect.y = min(0, self.description_slider_rect.y)
            self.description_slider_rect.y = max(self.description_surface.height - self.description_slider_surface.height, self.description_slider_rect.y)

    def create_keybinds(self):
        index = 0
        for key, value in self.options_data[0].items():
            symbol_image = pygame.image.load(value)
            pos = (10, 10 + 60 * index)
            key_setup = KeySetup(key, pos, symbol_image)
            self.keys_group.append(key_setup)
            index += 1
    

    # draw

    def draw_slider_bar(self):
        height1 = self.description_slider_surface.get_height()
        height2 = self.description_surface.get_height()
        Y1 = self.description_slider_rect.top

        coeff = height2 / height1
        slider_height = coeff * height2
        
        slide_bar_rect = pygame.Rect(0, 0, 10, slider_height)
        slide_bar_rect.right = self.description_rect.right - 2
        slide_bar_rect.top = self.description_rect.top - Y1 * coeff

        pygame.draw.rect(self.display_surface, 'grey', slide_bar_rect, 0, 4)


    def draw_keybinds(self):
        self.description_surface.fill('green')
        self.description_slider_surface.fill('green')

        for key in self.keys_group:
            key.draw(self.description_slider_surface)
        self.description_surface.blit(self.description_slider_surface, self.description_slider_rect)
        self.display_surface.blit(self.description_surface, self.description_rect.topleft)
        self.draw_slider_bar()
    
    def draw_slider(self):
        self.slider.draw(self.display_surface)

    def draw_description(self):
        pygame.draw.rect(self.display_surface, 'White', self.description_rect, 0, 4)
        self.description()

    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
        self.draw_description()


class ShopMenu(GeneralMenu):
    def __init__(self, player, switch_screen):
        options = ['wood', 'apple', 'hoe', 'water', 'corn', 'tomato', 'seed']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Shop'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)
    
    def button_action(self, text):
        self.switch_screen('level')

# ------- Components ------- #

class KeySetup:
    def __init__(self, key_name, pos, symbol_image):
        self.key_name = key_name
        self.key = pygame.K_UP
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

        # rect
        self.pos = pos
        self.rect = pygame.Rect(pos, (300, 50))

        # symbol
        self.symbol_image = symbol_image
        self.symbol_image = pygame.transform.scale(self.symbol_image, (40, 40))
        self.symbol_image_rect = self.symbol_image.get_rect(midright=self.rect.midright - vector(10, 0))
    
    def setup(self):
        pass

    # draw
    def draw_key_name(self, surface):
        text_surf = self.font.render(self.key_name, False, 'Black')
        text_rect = text_surf.get_frect(midleft=(self.rect.left + 10, self.rect.centery))
        pygame.draw.rect(surface, 'White', text_rect.inflate(10, 10), 0, 4)
        surface.blit(text_surf, text_rect)
    
    def draw_symbol(self, surface):
        if self.symbol_image:
            surface.blit(self.symbol_image, self.symbol_image_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, 'grey', self.rect, 0, 4)
        self.draw_key_name(surface)
        self.draw_symbol(surface)



class Button:
    def __init__(self, text, font, rect):
        self.font = font
        self.text = text
        self.rect = rect
        self.color = 'White'
        self.hover_active = False

        self.display_surface = pygame.display.get_surface()

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos())
    
    # draw
    def draw_text(self):
        text_surf = self.font.render(self.text, False, 'Black')
        text_rect = text_surf.get_frect(center=self.rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 4)
        else:
            self.hover_active = False

    def draw(self):
        pygame.draw.rect(self.display_surface, self.color, self.rect, 0, 4)
        self.draw_text()
        self.draw_hover()



class Slider:
    def __init__(self, rect, min_value, max_value, init_value, sounds):
        # sounds
        self.sounds = sounds
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

        # rect
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.value = init_value
        self.drag_active = False

        # knob
        self.knob_radius = 10

    def get_value(self):
        return self.value
    
    # events
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos()):
                self.drag_active = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.drag_active = False

        if event.type == pygame.MOUSEMOTION and self.drag_active:
            self.value = self.min_value + (self.max_value - self.min_value) * (mouse_pos()[0] - self.rect.left) / (self.rect.width - 10)
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.update_volume()
    
    def update_volume(self):
        self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
        for key in self.sounds:
            if key != 'music':
                self.sounds[key].set_volume((self.value / 100))

    # draw
    def draw_value(self, surface):
        text_surf = self.font.render(str(int(self.value)), False, 'Black')
        text_rect = text_surf.get_frect(midtop=(self.rect.centerx, self.rect.bottom + 10))
        surface.blit(text_surf, text_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, (220, 185, 138), self.rect, 0, 4)
        pygame.draw.rect(surface, (243, 229, 194), self.rect.inflate(-4, -4), 0, 4)
        knob_x = self.rect.left + (self.rect.width - 10) * (self.value - self.min_value) / (self.max_value - self.min_value)
        pygame.draw.circle(surface, (232, 207, 166), (int(knob_x), self.rect.centery), self.knob_radius)
        self.draw_value(surface)



