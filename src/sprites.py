from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

import pygame
import random

from pathfinding.core.grid import Grid as PF_Grid
from pathfinding.finder.a_star import AStarFinder as PF_AStarFinder

from src import settings
from src.menus import PauseMenu, SettingsMenu
from src.npc_behaviour import Selector, Sequence, Condition, Action
from src.npc_behaviour import Context as BehaviourContext
from src.settings import (
    APPLE_POS,
    GROW_SPEED,
    LAYERS,
    SCALE_FACTOR,
)

from src.enums import InventoryResource, FarmingTool, ItemToUse
from src import savefile

from src import support
from src import timer


class Sprite(pygame.sprite.Sprite):
    def __init__(self,
                 pos: tuple[int | float,
                            int | float],
                 surf: pygame.Surface,
                 groups: tuple[pygame.sprite.Group] | pygame.sprite.Group,
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
            entity.add_resource(InventoryResource.APPLE)
        if self.health < 0 and self.alive:
            entity.add_resource(InventoryResource.WOOD, 5)
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


class Entity(CollideableSprite, ABC):
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
        self.current_tool = FarmingTool.get_first_tool_id()
        self.tool_index = self.current_tool.value - FarmingTool.get_first_tool_id().value

        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool
        
        # seeds
        self.available_seeds = ['corn', 'tomato']
        self.current_seed = FarmingTool.get_first_seed_id()
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 0,
            InventoryResource.TOMATO_SEED: 0,
        }

        # Not all Entities can go to the market, so those that can't should not have money either
        self.money = 0

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

    # FIXME: Sometimes NPCs get stuck inside the player's hitbox
    def collision(self, direction) -> bool:
        """
        :return: true: Entity collides with a sprite in self.collision_sprites, otherwise false
        """
        colliding_rect = False

        for sprite in self.collision_sprites:
            if sprite is not self:

                # Entities should collide with their hitbox_rects to make them able to approach
                #  each other further than the empty space on their sprite images would allow
                if isinstance(sprite, Entity):
                    if sprite.hitbox_rect.colliderect(self.hitbox_rect):
                        colliding_rect = sprite.hitbox_rect
                elif sprite.rect.colliderect(self.hitbox_rect):
                    colliding_rect = sprite.rect

                if colliding_rect:
                    if direction == 'horizontal':
                        if self.direction.x > 0:
                            self.hitbox_rect.right = colliding_rect.left
                        if self.direction.x < 0:
                            self.hitbox_rect.left = colliding_rect.right
                    else:
                        if self.direction.y < 0:
                            self.hitbox_rect.top = colliding_rect.bottom
                        if self.direction.y > 0:
                            self.hitbox_rect.bottom = colliding_rect.top

        return bool(colliding_rect)

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
                    self.use_tool(ItemToUse.REGULAR_TOOL)
            else:
                # self.use_tool('tool')
                self.state = 'idle'
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option: ItemToUse):
        self.apply_tool((self.current_tool, self.current_seed)[option], self.get_target_pos(), self)

    def add_resource(self, resource, amount=1):
        # FIXME: Should be changed to a better method to refer from the "old" resource strings to the new enum values
        self.inventory[{"corn": InventoryResource.CORN,
                        "tomato": InventoryResource.TOMATO}[resource]] += amount

    def update(self, dt):
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)


# <editor-fold desc="NPC">
@dataclass
class NPCBehaviourContext(BehaviourContext):
    npc: "NPC"


# TODO: NPCs can not harvest fully grown crops on their own yet
class NPCBehaviourMethods:
    """
    Group of classes used for NPC behaviour.

    Attributes:
        behaviour:   Default NPC behaviour tree
    """
    behaviour = None

    @staticmethod
    def init():
        """
        Initialises the behaviour tree.
        """
        NPCBehaviourMethods.behaviour = Selector([
            Sequence([
                Condition(NPCBehaviourMethods.will_farm),
                Selector([
                    Sequence([
                        Condition(NPCBehaviourMethods.will_create_new_farmland),
                        Action(NPCBehaviourMethods.create_new_farmland)
                    ]),
                    Sequence([
                        Condition(NPCBehaviourMethods.will_plant_tilled_farmland),
                        Action(NPCBehaviourMethods.plant_random_seed)
                    ]),
                    Action(NPCBehaviourMethods.water_farmland)
                ])
            ]),
            Action(NPCBehaviourMethods.wander)
        ])

    @staticmethod
    def will_farm(context: NPCBehaviourContext) -> bool:
        """
        1 in 3 chance to go farming instead of wandering around
        :return: 1/3 true | 2/3 false
        """
        return random.randint(0, 2) is 0

    @staticmethod
    def will_create_new_farmland(context: NPCBehaviourContext) -> bool:
        """
        :return: True: untilled farmland available AND (all other farmland planted and watered OR 1/3), otherwise False
        """
        empty_farmland_available = 0
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "F" in entry:
                    if "X" not in entry:
                        empty_farmland_available += 1
                    else:
                        if "P" not in entry:
                            unplanted_farmland_available += 1
                        else:
                            if "W" not in entry:
                                unwatered_farmland_available += 1

        if empty_farmland_available <= 0:
            return False

        return (unplanted_farmland_available == 0 and unwatered_farmland_available == 0) or random.randint(0, 2) == 0

    @staticmethod
    def create_new_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random untilled but farmable tile, makes the NPC walk to and till it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "F" in entry and "X" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.HOE
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def will_plant_tilled_farmland(context: NPCBehaviourContext) -> bool:
        """
        :return: True if unplanted farmland available AND (all other farmland watered OR 3/4), otherwise False
        """
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "X" in entry:
                    if "P" not in entry:
                        unplanted_farmland_available += 1
                    else:
                        if "W" not in entry:
                            unwatered_farmland_available += 1

        if unplanted_farmland_available <= 0:
            return False

        return unwatered_farmland_available == 0 or random.randint(0, 3) <= 2

    @staticmethod
    def plant_random_seed(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unplanted but tilled tile, makes the NPC walk to and plant a random seed on it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "X" in entry and "P" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.current_seed = FarmingTool.CORN_SEED
            context.npc.seed_index = context.npc.current_seed.value - FarmingTool.get_first_seed_id().value
            context.npc.use_tool(ItemToUse(1))

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    # FIXME: When NPCs water the plants, the hoe is displayed as the item used instead of the watering can
    @staticmethod
    def water_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unwatered but planted tile, makes the NPC walk to and water it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "P" in entry and "W" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.WATERING_CAN
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def wander_to_interact(context: NPCBehaviourContext,
                           target_position: tuple[int, int],
                           on_path_completion: Callable[[], None]):
        """
        :return: True if path has successfully been created, otherwise False
        """

        if context.npc.create_path_to_tile(target_position):
            if len(context.npc.pf_path) > 1:
                facing = (context.npc.pf_path[-1][0] - context.npc.pf_path[-2][0],
                          context.npc.pf_path[-1][1] - context.npc.pf_path[-2][1])
            else:
                facing = (context.npc.pf_path[-1][0] - context.npc.rect.centerx / 64,
                          context.npc.pf_path[-1][1] - context.npc.rect.centery / 64)

            facing = (facing[0], 0) if abs(facing[0]) > abs(facing[1]) else (0, facing[1])

            # Deleting the final step of the path leads to the NPC always standing in reach of the tile they want to
            #  interact with (cf. Entity.get_target_pos)
            context.npc.pf_path.pop(-1)

            def inner():
                context.npc.direction.update(facing)
                context.npc.get_facing_direction()
                context.npc.direction.update((0, 0))

                on_path_completion()

                context.npc.pf_on_path_completion = lambda: None

            context.npc.pf_on_path_completion = inner
            return True
        return False

    @staticmethod
    def wander(context: NPCBehaviourContext) -> bool:
        """
        Makes the NPC wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """
        tile_size = settings.SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(context.npc.rect.centerx, context.npc.rect.centery) / tile_size

        # To limit the required computing power, the NPC currently only tries to navigate to
        #  11 random points in its immediate vicinity (5 tile radius)
        avail_x_coords = list(range(
            max(0, int(tile_coord.x) - 5),
            min(int(tile_coord.x) + 5, context.npc.pf_grid.width - 1) + 1
        ))

        avail_y_coords = list(range(
            max(0, int(tile_coord.y) - 5),
            min(int(tile_coord.y) + 5, context.npc.pf_grid.height - 1) + 1
        ))

        for i in range(min(len(avail_x_coords), len(avail_y_coords))):
            pos = (
                random.choice(avail_x_coords),
                random.choice(avail_y_coords)
            )
            avail_x_coords.remove(pos[0])
            avail_y_coords.remove(pos[1])

            if context.npc.create_path_to_tile(pos):
                break
        else:
            context.npc.pf_state = NPCState.IDLE
            context.npc.direction.update((0, 0))
            context.npc.pf_state_duration = 1
            return False
        return True


# TODO: Refactor NPCState into Entity.state (maybe override Entity.get_state())
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

    pf_on_path_completion: Callable[[], None]

    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            soil_layer,
            pf_matrix: list[list[int]],
            pf_grid: PF_Grid,
            pf_finder: PF_AStarFinder):

        self.soil_layer = soil_layer

        self.pf_matrix = pf_matrix
        self.pf_grid = pf_grid
        self.pf_finder = pf_finder
        self.pf_state = NPCState.IDLE
        self.pf_state_duration = 0
        self.pf_path = []
        self.pf_on_path_completion = lambda: None

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,

            (32 * SCALE_FACTOR, 32 * SCALE_FACTOR),
            # scales the hitbox down to the exact tile size

            apply_tool
        )

        self.speed = 150

        # TODO: Ensure that the NPC always has all needed seeds it needs in its inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
        }

    def create_path_to_tile(self, coord: tuple[int, int]) -> bool:
        if not self.pf_grid.walkable(coord[0], coord[1]):
            return False

        tile_size = settings.SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / tile_size

        self.pf_state = NPCState.MOVING
        self.pf_state_duration = 0

        self.pf_grid.cleanup()

        start = self.pf_grid.node(int(tile_coord.x), int(tile_coord.y))
        end = self.pf_grid.node(*[int(i) for i in coord])

        path_raw = self.pf_finder.find_path(start, end, self.pf_grid)

        # The first position in the path will always be removed as it is the same coordinate the NPC is already
        #  standing on. Otherwise, if the NPC is just standing a little bit off the center of its current coordinate, it
        #  may turn around quickly once it reaches it, if the second coordinate of the path points in the same direction
        #  as where the NPC was just standing.
        self.pf_path = [(i.x + .5, i.y + .5) for i in path_raw[0][1:]]

        if not self.pf_path:
            self.pf_state = NPCState.IDLE
            self.direction.update((0, 0))
            self.pf_state_duration = 1
            return False

        return True

    def move(self, dt):
        tile_size = settings.SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / tile_size

        if self.pf_state == NPCState.IDLE:
            self.pf_state_duration -= dt

            if self.pf_state_duration <= 0:
                NPCBehaviourMethods.behaviour.run(NPCBehaviourContext(self))

        if self.pf_state == NPCState.MOVING:
            if not self.pf_path:
                # runs in case the path has been emptied in the meantime
                #  (e.g. NPCBehaviourMethods.wander_to_interact created a path to a tile adjacent to the NPC)
                self.pf_state = NPCState.IDLE
                self.direction.update((0, 0))
                self.pf_state_duration = random.randint(2, 5)

                self.pf_on_path_completion()
                return

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

                    self.pf_on_path_completion()
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

                    # Rounding the direction leads to smoother animations,
                    #  e.g. if the distance vector was (-0.99, -0.01), the NPC would face upwards, although it moves
                    #  much more to the left than upwards, as the animation method favors vertical movement
                    #
                    # Maybe normalise the vector?
                    #  Currently, it is not necessary as the NPC is not moving diagonally yet,
                    #  unless it collides with another entity while it is in-between two coordinates
                    self.direction.update((round(dx / distance), round(dy / distance)))

            self.hitbox_rect.update((
                next_position[0] * tile_size - self.hitbox_rect.width / 2,
                self.hitbox_rect.top,
            ), self.hitbox_rect.size)
            colliding = self.collision('horizontal')

            self.hitbox_rect.update((
                self.hitbox_rect.left,
                next_position[1] * tile_size - self.hitbox_rect.height / 2
            ), self.hitbox_rect.size)
            colliding = colliding or self.collision('vertical')

            if colliding:
                self.pf_state = NPCState.IDLE
                self.direction.update((0, 0))
                self.pf_state_duration = 1

        self.rect.update((self.hitbox_rect.centerx - self.rect.width / 2,
                          self.hitbox_rect.centery - self.rect.height / 2), self.rect.size)
        self.plant_collide_rect.center = self.hitbox_rect.center
# </editor-fold>


_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Entity):
    def __init__(
            self,
            game,
            pos: settings.Coordinate,
            frames,
            groups,
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            interact: Callable,
            sounds: settings.SoundDict,
            font: pygame.font.Font):
      
        save_data = savefile.load_savefile()
        self.game = game

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
        
        self.current_tool = save_data.get("current_tool", FarmingTool.get_first_tool_id())
        self.tool_index = self.current_tool.value - 1
        
        self.current_seed = save_data.get("current_seed", FarmingTool.get_first_seed_id())
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
                )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def save(self):
        # We compact the inventory first, i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(self.current_tool, self.current_seed, self.money, compacted_inv)

    def input(self):
        keys = pygame.key.get_pressed()
        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.game.dm.showing_dialogue:
            self.game.dm.advance()
            if not self.game.dm.showing_dialogue:
                self.blocked = False
            return
        # movement
        if not self.tool_active and not self.blocked:
            if recent_keys[pygame.K_ESCAPE]:
                self.paused = not self.paused
                self.direction.y = 0
                self.direction.x = 0
                return
            if recent_keys[pygame.K_t]:
                if self.game.dm.showing_dialogue:
                    pass
                else:
                    self.game.dm.open_dialogue("test")
                    self.blocked = True
                return

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

            # tool switch
            if recent_keys[pygame.K_q]:
                self.tool_index = (self.tool_index + 1) % FarmingTool.get_tool_count()
                self.current_tool = FarmingTool(self.tool_index + FarmingTool.get_first_tool_id())

            # tool use
            if recent_keys[pygame.K_SPACE]:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if recent_keys[pygame.K_e]:
                self.seed_index = (self.seed_index + 1) % FarmingTool.get_seed_count()
                self.current_seed = FarmingTool(self.seed_index + FarmingTool.get_first_seed_id())

            # seed used
            if recent_keys[pygame.K_LCTRL]:
                self.use_tool(ItemToUse.SEED)

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

    def get_current_tool_string(self):
        return self.available_tools[self.tool_index]

    def get_current_seed_string(self):
        return self.available_seeds[self.seed_index]

    def add_resource(self, resource, amount=1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update(self, dt):
        self.input()
        super().update(dt)
