import pygame
from .settings import *
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_pressed


class pause_menu:
    def __init__(self, font):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.index = 0
        # options
        self.width = 400
        self.space = 10
        self.padding = 8
        self.pressed_settings = False
        self.pressed_play = False
        self.pressed_quit = False
        # entries
        self.options = ["Resume", "Options", "Main Menu"]
        # self.setup()
        self.buttons = []
        self.create_buttons()


    def create_buttons(self):

        self.main_rect = pygame.Rect(0, 0, 400, 400)
        self.main_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        button_width = 400
        button_height = 50
        generic_button_rect = pygame.Rect(self.main_rect.topleft, (button_width, button_height))
        for item in self.options:
            button = Button(item, self.font, generic_button_rect)
            self.buttons.append(button)
            generic_button_rect = generic_button_rect.move(0, button_height + self.space)

    def setup(self):

        # create the text surfaces
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(SCREEN_WIDTH / 2 - self.width / 2, self.menu_top, self.width, self.total_height)

        # buy / sell text surface
    def input(self):
        keys = pygame.key.get_just_pressed()

        self.index = (self.index + int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])) % len(self.options)

        if keys[pygame.K_SPACE]:
            current_item = self.options[self.index]
            if 'Resume' in current_item:
                if not self.pressed_quit:
                    self.pressed_play = True
                    self.index = 0
            if 'Options' in current_item:
                if not self.pressed_quit and not self.pressed_play:
                    self.pressed_settings = True
                    self.index = 0
            elif 'Main Menu' in current_item:
                if not self.pressed_play:
                    self.pressed_quit = True
                    self.index = 0

    def show_entry(self, text_surf, top, index, text_index):

        # background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_frect(midleft=(self.main_rect.left + (self.main_rect.width/2)-text_surf.get_width()/2, bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)

        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)

    def main_menu_title(self):
        text_surf = self.font.render('Pause Menu', False, 'Black')
        text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

        pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def click(self):
        self.index += 1
        if mouse_pressed()[0]:
            print(self.index)
            # for button in self.buttons:
            #     if button.active:
            #         current_item = button.text
            #         if 'Resume' in current_item:
            #             if not self.pressed_quit:
            #                 self.pressed_play = True
            #         if 'Options' in current_item:
            #             if not self.pressed_quit and not self.pressed_play:
            #                 self.pressed_settings = True
            #         if 'Main Menu' in current_item:
            #             if not self.pressed_play:
            #                 self.pressed_quit = True

    def draw_buttons(self):
        for button in self.buttons:
            button.draw()


    def update(self):
        # self.input()
        self.click()
        self.main_menu_title()
        self.draw_buttons()
        # for text_index, text_surf in enumerate(self.text_surfs):
        #     top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
        #     self.show_entry(text_surf, top, self.index, text_index)



class Button:
    def __init__(self, text, font, rect):
        self.font = font
        self.text = text
        self.rect = rect
        self.color = 'White'
        self.hover_active = False

        self.display_surface = pygame.display.get_surface()


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

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos())
        

    def draw(self):
        pygame.draw.rect(self.display_surface, self.color, self.rect, 0, 4)
        self.draw_text()
        self.draw_hover()
        

