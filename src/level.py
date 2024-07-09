import math
import sys

import pygame  # noqa

from pathfinding.core.grid import Grid as PF_Grid
from pathfinding.finder.a_star import AStarFinder as PF_AStarFinder

from src import settings
from src.groups import AllSprites
from src.soil import SoilLayer
from src.support import get_object_hitboxes
from src.transition import Transition
from random import randint
from src.sky import Sky, Rain
from src.overlay import Overlay
from src.shop import Menu
from src.sprites import (
    AnimatedSprite,
    ParticleSprite,
    Tree,
    Sprite,
    Player,
    NPC, NPCBehaviourMethods, CollideableSprite,
)
from src.enums import FarmingTool, GameState
from src.settings import (
    TILE_SIZE,
    SCALE_FACTOR,
    LAYERS,
    MapDict,
)


class Level:

    def __init__(self, game, tmx_maps: MapDict, character_frames, level_frames, overlay_frames, font, sounds, switch):
        self.display_surface = pygame.display.get_surface()
        self.game = game

        # sprite groups
        self.entities = {}
        self.npcs = {}
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        self.font = font

        # pathfinding
        self.pf_matrix = []
        self.pf_grid: PF_Grid
        self.pf_finder = PF_AStarFinder()

        # soil
        self.soil_layer = SoilLayer(
            self.all_sprites,
            self.collision_sprites,
            tmx_maps['main'],
            level_frames)
        self.raining = False

        # sounds
        self.sounds = sounds

        # data
        self.setup(tmx_maps, character_frames, level_frames)
        self.transition = Transition(self.reset, self.finish_reset)
        self.day_transition = False
        self.current_day = 0

        # weather
        self.sky = Sky()
        self.rain = Rain(
            self.all_sprites,
            level_frames,
            (tmx_maps['main'].width *
             TILE_SIZE *
             SCALE_FACTOR,
             tmx_maps['main'].height *
             TILE_SIZE *
             SCALE_FACTOR))

        # overlays
        self.overlay = Overlay(self.entities['Player'], overlay_frames)
        self.menu = Menu(self.entities['Player'], self.toggle_shop, font)
        self.shop_active = False

        # switch
        self.switch_screen = switch

    def setup(self, tmx_maps: MapDict, character_frames, level_frames):
        self.sounds["music"].set_volume(0.1)
        self.sounds["music"].play(-1)

        matrix_width = tmx_maps['main'].width
        matrix_height = tmx_maps['main'].height

        # environment
        for layer in ['Lower ground', 'Upper ground']:
            for x, y, surf in tmx_maps['main'].get_layer_by_name(
                    layer).tiles():
                Sprite((x * TILE_SIZE * SCALE_FACTOR,
                        y * TILE_SIZE * SCALE_FACTOR),
                       pygame.transform.scale_by(surf,
                                                 SCALE_FACTOR),
                       self.all_sprites,
                       LAYERS['lower ground'])

        self.pf_matrix = [[1 for _ in range(matrix_width)] for _ in range(matrix_height)]

        # water
        for x, y, surf in tmx_maps['main'].get_layer_by_name('Water').tiles():
            AnimatedSprite((x * TILE_SIZE * SCALE_FACTOR,
                            y * TILE_SIZE * SCALE_FACTOR),
                           level_frames['animations']['water'],
                           self.all_sprites,
                           LAYERS['water'])

        collidable_object_hitboxes = get_object_hitboxes("data/tilesets/objects.tsx")

        # objects
        for obj in tmx_maps['main'].get_layer_by_name('Collidable objects'):
            if obj.name == 'Tree':
                Tree((obj.x * SCALE_FACTOR,
                      obj.y * SCALE_FACTOR),
                     pygame.transform.scale_by(obj.image,
                                               SCALE_FACTOR),
                     (self.all_sprites,
                      self.collision_sprites,
                      self.tree_sprites),
                     collidable_object_hitboxes.get(obj.properties.get("id")),
                     obj.name,
                     level_frames['objects']['apple'],
                     level_frames['objects']['stump'])
            else:
                hitbox = collidable_object_hitboxes.get(obj.properties.get("id"))
                x = CollideableSprite((obj.x * SCALE_FACTOR,
                        obj.y * SCALE_FACTOR),
                       pygame.transform.scale_by(obj.image,
                                                 SCALE_FACTOR),
                       (self.all_sprites,
                        self.collision_sprites),
                                      (0, 0))
                x.hitbox_rect = pygame.rect.Rect(
                    x.rect.left + hitbox[0] * settings.SCALE_FACTOR,
                    x.rect.top + hitbox[1] * settings.SCALE_FACTOR,
                    hitbox[2] * settings.SCALE_FACTOR,
                    hitbox[3] * settings.SCALE_FACTOR,
                )

            tile_x = int(obj.x / 16)
            tile_y = int(obj.y / 16)
            tile_w = math.ceil((obj.x + obj.width) / 16) - tile_x
            tile_h = math.ceil((obj.y + obj.height) / 16) - tile_y

            for w in range(tile_w):
                for h in range(tile_h):
                    self.pf_matrix[tile_y + h][tile_x + w] = 0

        # collisions
        for obj in tmx_maps['main'].get_layer_by_name('Collisions'):
            Sprite(
                (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                pygame.Surface((
                    obj.width * SCALE_FACTOR,
                    obj.height * SCALE_FACTOR,
                )),
                (self.collision_sprites,),
            )

            tile_x = int(obj.x / 16)
            tile_y = int(obj.y / 16)
            tile_w = math.ceil((obj.x + obj.width) / 16) - tile_x
            tile_h = math.ceil((obj.y + obj.height) / 16) - tile_y

            for w in range(tile_w):
                for h in range(tile_h):
                    self.pf_matrix[tile_y + h][tile_x + w] = 0

        self.pf_grid = PF_Grid(matrix=self.pf_matrix)
        self.pf_finder = PF_AStarFinder()

        # interactions
        for obj in tmx_maps['main'].get_layer_by_name('Interactions'):
            Sprite((obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                   pygame.Surface((obj.width * SCALE_FACTOR, obj.height *
                                  SCALE_FACTOR)), (self.interaction_sprites,),
                   LAYERS['main'], obj.name)

        # playable entities
        self.entities = {}
        for obj in tmx_maps['main'].get_layer_by_name('Entities'):
            self.entities[obj.name] = Player(
                game=self.game,
                pos=(obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                hitbox=(18, 26, 12, 6),
                frames=character_frames['rabbit'],
                groups=(self.all_sprites, self.collision_sprites),
                collision_sprites=self.collision_sprites,
                apply_tool=self.apply_tool,
                interact=self.interact,
                sounds=self.sounds,
                font=self.font,
            )

        # non-playable entities
        if settings.ENABLE_NPCS:
            NPCBehaviourMethods.init()
            self.npcs = {}
            for obj in tmx_maps['main'].get_layer_by_name('NPCs'):
                self.npcs[obj.name] = NPC(
                    pos=(obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                    hitbox=(18, 26, 12, 6),
                    frames=character_frames['rabbit'],
                    groups=(self.all_sprites, self.collision_sprites),
                    collision_sprites=self.collision_sprites,
                    apply_tool=self.apply_tool,
                    soil_layer=self.soil_layer,
                    pf_matrix=self.pf_matrix,
                    pf_grid=self.pf_grid,
                    pf_finder=self.pf_finder,
                )

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.switch_screen(GameState.PAUSE)

    def apply_tool(self, tool: FarmingTool, pos, entity):
        match tool:
            case FarmingTool.AXE:
                for tree in self.tree_sprites:
                    if tree.rect.collidepoint(pos):
                        tree.hit(entity)
                        self.sounds['axe'].play()
            case FarmingTool.HOE:
                self.soil_layer.hoe(pos, hoe_sound=self.sounds['hoe'])
            case FarmingTool.WATERING_CAN:
                self.soil_layer.water(pos)
                self.sounds['water'].play()
            case _:  # All seeds
                self.soil_layer.plant_seed(pos, entity.available_seeds[tool - FarmingTool.get_first_seed_id()],
                                           entity.inventory, plant_sounds=[self.sounds['plant'],
                                                                           self.sounds['cant_plant']])

    def create_particle(self, sprite):
        ParticleSprite(sprite.rect.topleft, sprite.image, (self.all_sprites,))

    def interact(self, pos):
        collided_interaction_sprite = pygame.sprite.spritecollide(
            self.entities['Player'], self.interaction_sprites, False)
        if collided_interaction_sprite:
            if collided_interaction_sprite[0].name == 'Bed':
                self.start_reset()
            if collided_interaction_sprite[0].name == 'Trader':
                self.toggle_shop()

    def reset(self):
        self.current_day += 1

        # plants
        self.soil_layer.update_plants()

        self.sky.set_time(6, 0)  # set to 0600 hours upon sleeping

        # soil
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        # apples on the trees

        # No need to iterate using explicit sprites() call.
        # Iterating over a sprite group normally will do the same thing
        for tree in self.tree_sprites:
            for apple in tree.apple_sprites:
                apple.kill()
            tree.create_fruit()

        # sky
        self.sky.start_color = [255, 255, 255]

    def finish_reset(self):
        self.day_transition = False
        for entity in self.entities.values():
            entity.blocked = False

    def start_reset(self):
        self.day_transition = True
        for entity in self.entities.values():
            entity.blocked = True
            entity.direction = pygame.Vector2(0, 0)

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(
                        self.entities['Player'].plant_collide_rect):
                    plant.kill()
                    self.entities['Player'].add_resource(plant.seed_type, 3)
                    self.create_particle(plant)
                    self.soil_layer.grid[
                        int(plant.rect.centery / (TILE_SIZE * SCALE_FACTOR))
                    ][
                        int(plant.rect.centerx / (TILE_SIZE * SCALE_FACTOR))
                    ].remove('P')

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def update(self, dt):
        self.display_surface.fill('gray')
        self.event_loop()

        if not self.shop_active:
            self.all_sprites.update(dt)

        self.all_sprites.draw(self.entities['Player'].rect.center)
        self.plant_collision()

        self.overlay.display(self.sky.get_time())
        self.sky.display(dt)

        if self.shop_active:
            self.menu.update()

        if self.raining and not self.shop_active:
            self.rain.update()

        if self.day_transition:
            self.transition.play()

        for npc in self.npcs.values():
            pygame.draw.rect(self.display_surface, (255, 0, 0),
                             (npc.hitbox_rect.x - (self.entities["Player"].rect.x - self.display_surface.get_width() / 2) - self.entities["Player"].rect.width / 2,
                              npc.hitbox_rect.y - (self.entities["Player"].rect.y - self.display_surface.get_height() / 2) - self.entities["Player"].rect.width / 2,
                              npc.hitbox_rect.width, npc.hitbox_rect.height),
                             2)

        pygame.draw.rect(self.display_surface, (0, 0, 255),
                         (self.entities["Player"].hitbox_rect.x - (self.entities["Player"].rect.x - self.display_surface.get_width() / 2) - self.entities["Player"].rect.width / 2,
                          self.entities["Player"].hitbox_rect.y - (self.entities["Player"].rect.y - self.display_surface.get_height() / 2) - self.entities["Player"].rect.height / 2,
                          self.entities["Player"].hitbox_rect.width, self.entities["Player"].hitbox_rect.height),
                         2)
