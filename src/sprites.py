from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Callable

import pygame
import random

from pathfinding.core.grid import Grid as PF_Grid
from pathfinding.finder.a_star import AStarFinder as PF_AStarFinder

from src import settings
from src.settings import (
    APPLE_POS,
    GROW_SPEED,
    LAYERS,
    SCALE_FACTOR,
)

from src import support
from src import timer
from src.pause_menu import PauseMenu
from src.settings_menu import SettingsMenu


class Sprite(pygame.sprite.Sprite):
    def __init__(self,
                 pos: tuple[int | float,
                            int | float],
                 surf: pygame.Surface,
                 groups: tuple[pygame.sprite.Group],
                 z: int = LAYERS['main'],
                 name: str | None = None):
        super().__init__(groups)
        self.surf = surf
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.name = name


class ParticleSprite(Sprite):
    def __init__(self, pos, surf, groups, duration=300):
        white_surf = pygame.mask.from_surface(surf).to_surface()
        white_surf.set_colorkey('black')
        super().__init__(pos, white_surf, groups, LAYERS['particles'])
        self.timer = timer.Timer(duration, autostart=True, func=self.kill)

    def update(self, dt):
        self.timer.update()


class CollideableSprite(Sprite):
    def __init__(self, pos, surf, groups, shrink, z=LAYERS['main']):
        super().__init__(pos, surf, groups, z)
        self.hitbox_rect = self.rect.inflate(-shrink[0], -shrink[1])


class Plant(CollideableSprite):
    def __init__(self, seed_type, groups, soil_sprite, frames, check_watered):
        super().__init__(soil_sprite.rect.center,
                         frames[0], groups, (0, 0), LAYERS['plant'])
        self.rect.center = soil_sprite.rect.center + \
            pygame.Vector2(0.5, -3) * SCALE_FACTOR
        self.soil = soil_sprite
        self.check_watered = check_watered
        self.frames = frames
        self.hitbox = None

        self.seed_type = seed_type
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[seed_type]
        self.harvestable = False

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_frect(
                midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, 2))


class Tree(CollideableSprite):
    def __init__(self, pos, surf, groups, name, apple_surf, stump_surf):
        super().__init__(
            pos,
            surf,
            groups,
            (30 * SCALE_FACTOR, 20 * SCALE_FACTOR),
        )
        self.name = name
        self.part_surf = support.generate_particle_surf(self.image)
        self.apple_surf = apple_surf
        self.stump_surf = stump_surf
        self.health = 5
        self.timer = timer.Timer(300, func=self.unhit)
        self.hitbox = None
        self.was_hit = False
        self.alive = True
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

    def unhit(self):
        self.was_hit = False
        if self.health < 0:
            self.image = self.stump_surf
            if self.alive:
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.hitbox = self.rect.inflate(-10, -self.rect.height * 0.6)
                self.alive = False
        elif self.health >= 0 and self.alive:
            self.image = self.surf

    def create_fruit(self):
        for pos in APPLE_POS['default']:
            if random.randint(0, 10) < 6:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Sprite((x, y), self.apple_surf, (self.apple_sprites,
                       self.groups()[0]), LAYERS['fruit'])

    def update(self, dt):
        self.timer.update()

    def hit(self, entity):
        if self.was_hit:
            return
        self.was_hit = True
        self.health -= 1
        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = random.choice(self.apple_sprites.sprites())
            random_apple.kill()
            entity.add_resource('apple')
        if self.health < 0 and self.alive:
            entity.add_resource("wood", 5)
        self.image = support.generate_particle_surf(self.image)
        self.timer.activate()


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, frames[0], groups, z)

    def animate(self, dt):
        self.frame_index += 2 * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def update(self, dt):
        self.animate(dt)


class WaterDrop(Sprite):
    def __init__(self, pos, surf, groups, moving, z):
        super().__init__(pos, surf, groups, z)
        self.timer = timer.Timer(
            random.randint(400, 600),
            autostart=True,
            func=self.kill,
        )
        self.start_time = pygame.time.get_ticks()
        self.moving = moving

        if moving:
            self.direction = pygame.Vector2(-2, 4)
            self.speed = random.randint(200, 250)

    def update(self, dt):
        self.timer.update()
        if self.moving:
            self.rect.topleft += self.direction * self.speed * dt


class Entity(ABC, CollideableSprite):
    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            shrink: tuple[int, int],
            apply_tool: Callable,
            z=LAYERS['main']):

        self.frames = frames
        self.frame_index = 0
        self.state = 'idle'
        self.facing_direction = 'down'

        super().__init__(
            pos,
            self.frames[self.state][self.facing_direction][self.frame_index],
            groups,
            shrink,
            z=z
        )

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_sprites = collision_sprites
        self.plant_collide_rect = self.hitbox_rect.inflate(10, 10)

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.tool_index = 0
        self.current_tool = self.available_tools[self.tool_index]
        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.available_seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.current_seed = self.available_seeds[self.seed_index]

        # inventory
        self.inventory = {
            'wood': 20,
            'apple': 20,
            'corn': 20,
            'tomato': 20,
            'tomato seed': 5,
            'corn seed': 5,
        }
        self.money = 200

    def get_state(self):
        self.state = 'walk' if self.direction else 'idle'

    def get_facing_direction(self):
        # prioritizes vertical animations, flip if statements to get horizontal
        # ones
        if self.direction.x:
            self.facing_direction = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y:
            self.facing_direction = 'down' if self.direction.y > 0 else 'up'

    def get_target_pos(self):
        vectors = {
            'left': pygame.Vector2(-1, 0),
            'right': pygame.Vector2(1, 0),
            'down': pygame.Vector2(0, 1),
            'up': pygame.Vector2(0, -1),
        }
        return self.rect.center + vectors[self.facing_direction] * 40

    @abstractmethod
    def move(self, dt):
        pass

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top

    def animate(self, dt):
        current_animation = self.frames[self.state][self.facing_direction]
        self.frame_index += 4 * dt
        if not self.tool_active:
            self.image = current_animation[int(
                self.frame_index) % len(current_animation)]
        else:
            tool_animation = self.frames[self.available_tools[self.tool_index]
                                         ][self.facing_direction]
            if self.frame_index < len(tool_animation):
                self.image = tool_animation[min(
                    (round(self.frame_index), len(tool_animation) - 1))]
                if round(self.frame_index) == len(tool_animation) - \
                        1 and not self.just_used_tool:
                    self.just_used_tool = True
                    self.use_tool('tool')
            else:
                # self.use_tool('tool')
                self.state = 'idle'
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option):
        self.apply_tool(
            self.current_tool if option == 'tool' else self.current_seed,
            self.get_target_pos(),
            self)

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount

    def update(self, dt):
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)


class NPCState(IntEnum):
    IDLE = 0
    MOVING = 1


class NPC(Entity):
    # Pathfinding
    pf_matrix: list[list[int]]
    """A representation of the in-game tilemap,
       where 1 stands for a walkable tile, and 0 stands for a non-walkable tile.
       Each list entry represents one row of the tilemap."""

    pf_grid: PF_Grid
    pf_finder: PF_AStarFinder
    pf_state: NPCState

    pf_path: list[tuple[int, int]]
    """The current path on which the NPC is moving.
       Each tile on which the NPC is moving is represented by its own coordinate tuple,
       while the first one in the list always being the NPCs current target position."""

    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            pf_matrix: list[list[int]],
            pf_grid: PF_Grid,
            pf_finder: PF_AStarFinder):

        self.pf_matrix = pf_matrix
        self.pf_grid = pf_grid
        self.pf_finder = pf_finder
        self.pf_state = NPCState.IDLE
        self.pf_state_duration = 0
        self.pf_path = []

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,
            (44 * SCALE_FACTOR, 40 * SCALE_FACTOR),
            apply_tool
        )

    def move(self, dt):
        tile_size = settings.SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / tile_size

        if self.pf_state == NPCState.IDLE:
            self.pf_state_duration -= dt

            if self.pf_state_duration <= 0:
                self.pf_state = NPCState.MOVING
                self.pf_state_duration = 0

                # To limit the required computing power, the NPC currently only tries to navigate to
                #  11 random points in its immediate vicinity (5 tile radius)
                avail_x_coords = list(range(
                    max(0, int(tile_coord.x) - 5),
                    min(int(tile_coord.x) + 5, self.pf_grid.width - 1) + 1
                ))

                avail_y_coords = list(range(
                    max(0, int(tile_coord.y) - 5),
                    min(int(tile_coord.y) + 5, self.pf_grid.height - 1) + 1
                ))

                target_pos = tuple(tile_coord)

                for i in range(min(len(avail_x_coords), len(avail_y_coords))):
                    pos = (
                        random.choice(avail_x_coords),
                        random.choice(avail_y_coords)
                    )
                    avail_x_coords.remove(pos[0])
                    avail_y_coords.remove(pos[1])

                    if self.pf_grid.walkable(pos[0], pos[1]):
                        target_pos = pos
                        break

                self.pf_grid.cleanup()

                start = self.pf_grid.node(int(tile_coord.x), int(tile_coord.y))
                end = self.pf_grid.node(*[int(i) for i in target_pos])

                path_raw = self.pf_finder.find_path(start, end, self.pf_grid)

                self.pf_path = [(i.x + .5, i.y + .5) for i in path_raw[0]]

                if not self.pf_path:
                    self.pf_state = NPCState.IDLE
                    self.direction.update((0, 0))
                    self.pf_state_duration = 2

        if self.pf_state == NPCState.MOVING:
            next_position = (tile_coord.x, tile_coord.y)

            # remaining distance the npc moves in the current frame
            remaining_distance = self.speed * dt / tile_size

            while remaining_distance:
                if next_position == self.pf_path[0]:
                    # the NPC reached its current target position
                    self.pf_path.pop(0)

                if not len(self.pf_path):
                    # the NPC has completed its path
                    self.pf_state = NPCState.IDLE
                    self.direction.update((0, 0))
                    self.pf_state_duration = random.randint(2, 5)
                    break

                # x- and y-distances from the NPCs current position to its target position
                dx = self.pf_path[0][0] - next_position[0]
                dy = self.pf_path[0][1] - next_position[1]

                distance = (dx ** 2 + dy ** 2) ** 0.5

                if remaining_distance >= distance:
                    # the NPC reaches its current target position in the current frame
                    next_position = self.pf_path[0]
                    remaining_distance -= distance
                else:
                    # the NPC does not reach its current target position in the current frame,
                    #  so it continues to move towards it
                    next_position = (
                        next_position[0] + dx * remaining_distance / distance,
                        next_position[1] + dy * remaining_distance / distance
                    )
                    remaining_distance = 0
                    self.direction.update((dx / distance, dy / distance))

            # TODO: NPC <-> Player collision

            self.hitbox_rect.update((
                next_position[0] * tile_size - self.hitbox_rect.width / 2,
                self.hitbox_rect.top,
            ), self.hitbox_rect.size)
            self.collision('horizontal')

            self.hitbox_rect.update((
                self.hitbox_rect.left,
                next_position[1] * tile_size - self.hitbox_rect.height / 2
            ), self.hitbox_rect.size)
            self.collision('vertical')

        self.rect.update((self.hitbox_rect.centerx - self.rect.width / 2,
                          self.hitbox_rect.centery - self.rect.height / 2), self.rect.size)
        self.plant_collide_rect.center = self.hitbox_rect.center


class Player(Entity):
    def __init__(
            self,
            pos: settings.Coordinate,
            frames,
            groups,
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            interact: Callable,
            sounds: settings.SoundDict,
            font: pygame.font.Font):

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,
            (44 * SCALE_FACTOR, 40 * SCALE_FACTOR),
            apply_tool
        )

        # movement
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact
        self.sounds = sounds

        # menus
        self.pause_menu = PauseMenu(self.font)
        self.settings_menu = SettingsMenu(self.font, self.sounds)

        # sounds
        self.sounds = sounds

    def input(self):
        keys = pygame.key.get_pressed()
        # movement
        if not self.tool_active and not self.blocked:
            recent_keys = pygame.key.get_just_pressed()
            if recent_keys[pygame.K_ESCAPE]:
                self.paused = not self.paused
                self.direction.y = 0
                self.direction.x = 0

        if not self.tool_active and not self.blocked and not self.paused:
            self.direction.x = int(
                keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(
                keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.direction = (
                self.direction.normalize()
                if self.direction
                else self.direction
            )

            recent_keys = pygame.key.get_just_pressed()
            # tool switch
            if recent_keys[pygame.K_q]:
                self.tool_index = (self.tool_index +
                                   1) % len(self.available_tools)
                self.current_tool = self.available_tools[self.tool_index]

            # tool use
            if recent_keys[pygame.K_SPACE]:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool in {'hoe', 'axe'}:
                    self.sounds['swing'].play()

            # seed switch
            if recent_keys[pygame.K_e]:
                self.seed_index = (
                    self.seed_index + 1
                ) % len(self.available_seeds)
                self.current_seed = self.available_seeds[self.seed_index]

            # seed used
            if recent_keys[pygame.K_LCTRL]:
                self.use_tool('seed')

                # interact
            if recent_keys[pygame.K_RETURN]:
                self.interact(self.rect.center)

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center
        self.plant_collide_rect.center = self.hitbox_rect.center

    def add_resource(self, resource, amount=1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update(self, dt):
        self.input()
        super().update(dt)
