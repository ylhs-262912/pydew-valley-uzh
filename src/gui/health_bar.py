import random
import pygame

from src.settings import SCALE_FACTOR
from src.support import import_image

class HealthProgressBar(pygame.sprite.Sprite):
    def __init__(self, hp):
        super().__init__()
        self.pos = (50, 60)

        # storing all three cat images
        self.cat_imgs = []
        for i in range(3):
            img = import_image(f'images/health_bar/health_cat_{i + 1}.png')
            img = pygame.transform.scale(img, (30 * SCALE_FACTOR * 0.7, 28 * SCALE_FACTOR * 0.7))
            rect = img.get_rect(center=(self.pos[0], self.pos[1] + 20))
            self.cat_imgs.append([img, rect])
        self.curr_cat = 0 # current cat index.

        # health bar
        self.health_bar = pygame.transform.scale(import_image('images/health_bar/health_bar.png', True),
                                                 (70 * SCALE_FACTOR * 0.8, 14 * SCALE_FACTOR * 0.8))
        self.health_bar_rect = self.health_bar.get_rect()
        self.health_bar_rect.topleft = self.pos

        # health (inside the health bar).
        self.color = (255, 255, 255)
        self.health = [(0, 0), (65, 0), (69, 4), (69, 9), (65, 13), (0, 13)]
        # setting position w.r.t to self.pos
        for i in range(len(self.health)):
            self.health[i] = [self.pos[0] + 1 + self.health[i][0] * SCALE_FACTOR * 0.8,
                              self.pos[1] + 1 + self.health[i][1] * SCALE_FACTOR * 0.8]

        # health points
        self.hp = hp # health points
        # self.per_width_hp will be substract / added as per intensity.
        self.per_width_hp = self.health_bar_rect.width / self.hp

        # shake
        self.SHAKE_INTENSITY = 1.5

        # colors for health bar.
        self.colors = {
            'Red': pygame.Color(255, 0, 0),
            'Yellow': pygame.Color(255, 255, 0),
            'Green': pygame.Color(0, 255, 0),
        }

    def render(self, screen):
        health_percent = (self.health[1][0] - self.pos[0]) / self.health_bar_rect.width
        if health_percent <= 0.25:
            offset = (random.uniform(-1, 1) * self.SHAKE_INTENSITY,
                      random.uniform(-1, 1) * self.SHAKE_INTENSITY)
        else:
            offset = (0, 0)

        # cat img changing.
        if health_percent > 0.5:
            self.curr_cat = 0
        elif health_percent <= 0.5 and health_percent > 0.25:
            self.curr_cat = 1
        else:
            self.curr_cat = 2
        pygame.draw.polygon(screen, self.color, [(coord[0] + offset[0], coord[1] + offset[1]) for coord in self.health])
        screen.blit(self.health_bar, (self.health_bar_rect.x + offset[0], self.health_bar_rect.y + offset[1]))
        cat_img, cat_rect = self.cat_imgs[self.curr_cat]
        screen.blit(cat_img, (cat_rect.x + offset[0], cat_rect.y + offset[1]))

    def apply_damage(self, intensity):
        if self.health[1][0] > self.health_bar_rect.left:
            for points in self.health[1:-1]:
                points[0] -= intensity * self.per_width_hp
            self.hp -= intensity
        else:
            self.health[1][0] = self.health_bar_rect.left
            self.health[4][0] = self.health_bar_rect.left

    def apply_health(self, intensity):
        # - 3 to hide the pixels from extending health bar container.
        if self.health[2][0] < self.health_bar_rect.right - 3:
            for points in self.health[1:-1]:
                points[0] += intensity * self.per_width_hp
            self.hp += intensity
        else:
            self.health[2][0] = self.health_bar_rect.right - 3
            self.health[3][0] = self.health_bar_rect.right - 3

    def change_color(self):
        health_percent = abs((self.health[1][0] - self.pos[0]) / self.health_bar_rect.width)
        if health_percent > 0.5:
            factor = (health_percent - 0.5) * 2
            self.color = self.colors['Yellow'].lerp(self.colors['Green'], factor)
        else:
            factor = health_percent * 2
            self.color = self.colors['Red'].lerp(self.colors['Yellow'], factor)

    def update(self, screen, dt):
        self.change_color()
        self.render(screen)