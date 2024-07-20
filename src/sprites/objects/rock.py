from src.sprites.base import CollideableSprite
from src.settings import LAYERS


class Rock(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Rock')
        self.hitbox_rect = self.rect.inflate(-10, -30)
        self.hitbox_rect.midbottom = self.rect.midbottom