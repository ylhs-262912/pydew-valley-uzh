import math
from collections.abc import Callable
from typing import Any

import pygame
from pytmx import TiledMap, TiledTileLayer, TiledObjectGroup, TiledObject

from src.enums import Layer, FarmingTool
from src.groups import AllSprites, PersistentSpriteGroup
from src.gui.interface.emotes import NPCEmoteManager, PlayerEmoteManager
from src.map_objects import MapObjects
from src.npc.bases.animal import Animal
from src.npc.chicken import Chicken
from src.npc.cow import Cow
from src.npc.npc import NPC
from src.npc.setup import AIData
from src.overlay.soil import SoilLayer
from src.settings import (
    SETUP_PATHFINDING, ENABLE_NPCS, TEST_ANIMALS,
    SCALED_TILE_SIZE, SCALE_FACTOR, TILE_SIZE
)
from src.sprites.base import Sprite, AnimatedSprite, CollideableMapObject
from src.sprites.character import Character
from src.sprites.entities.player import Player
from src.sprites.objects.tree import Tree
from src.sprites.setup import ENTITY_ASSETS


def _setup_tile_layer(
        layer: TiledTileLayer,
        func: Callable[[tuple[int, int], pygame.Surface], None]
):
    """
    Calls func for each tile found in layer
    :param layer: TiledTileLayer
    :param func: function(pos, image)
    """
    for x, y, image in layer.tiles():
        x = x * SCALED_TILE_SIZE
        y = y * SCALED_TILE_SIZE
        pos = (x, y)
        func(pos, image)


def _setup_object_layer(
        layer: TiledObjectGroup,
        func: Callable[[tuple[float, float], TiledObject], Any]
):
    """
    Calls func for each tile found in layer
    :param layer: TiledTileLayer
    :param func: function(pos, object) -> object instance
    :return: All object instances
    """
    objects = []
    for obj in layer:
        x = obj.x * SCALE_FACTOR
        y = obj.y * SCALE_FACTOR
        pos = (x, y)
        objects.append(func(pos, obj))
    return objects


class InvalidMapException(Exception):
    pass


class GameMap:
    """
    Class representing a single game map

    Attributes:
        _tilemap: loaded map as pytmx.TiledMap
        _tilemap_size: size of the current map (tile-scale)
        _tilemap_scaled_size: size of the current map (pixel-scale)

        _map_objects: Objects that have been loaded with custom hitboxes
                      TODO: This should probably be reworked to only load on
                       game start, as all maps are loaded on game start as well

        _pf_matrix: pathfinding matrix

        player_spawnpoint: default spawnpoint for the player
        player_entrances: points where the player should enter the map,
                          depending on which map they came from
        map_exits: collision sprites where the player should exit the map

        npcs: list of all NPCs on the map
        animals: list of all Animals on the map
    """
    _tilemap: TiledMap
    _tilemap_size: tuple[int, int]
    _tilemap_scaled_size: tuple[int, int]

    _map_objects: MapObjects

    # pathfinding
    _pf_matrix: list[list[int]]

    # map traversing points
    player_spawnpoint: tuple[int, int] | None
    player_entrances: dict[str, tuple[int, int]]
    map_exits: pygame.sprite.Group

    # non-player entities
    npcs: list[NPC]
    animals: list[Animal]

    def __init__(
            self,
            tilemap: TiledMap,

            # Sprite groups
            all_sprites: AllSprites,
            collision_sprites: PersistentSpriteGroup,
            interaction_sprites: PersistentSpriteGroup,
            tree_sprites: PersistentSpriteGroup,
            map_exits: pygame.sprite.Group,

            # Player instance
            player: Player,

            # Emote manager instances
            player_emote_manager: PlayerEmoteManager,
            npc_emote_manager: NPCEmoteManager,

            # SoilLayer and Tool applying function for farming NPCs
            soil_layer: SoilLayer,
            apply_tool: Callable[
                [FarmingTool, tuple[float, float], Character], None
            ],

            # assets
            frames: dict,
    ):
        self._tilemap = tilemap

        self.map_exits = map_exits

        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.interaction_sprites = interaction_sprites
        self.tree_sprites = tree_sprites

        self.player = player

        self.player_emote_manager = player_emote_manager
        self.npc_emote_manager = npc_emote_manager

        self.soil_layer = soil_layer
        self.apply_tool = apply_tool

        self.frames = frames

        self._tilemap_size = (
            self._tilemap.width,
            self._tilemap.height
        )
        self._tilemap_scaled_size = (
            self._tilemap_size[0] * SCALED_TILE_SIZE,
            self._tilemap_size[1] * SCALED_TILE_SIZE
        )

        # pathfinding
        self._pf_matrix = [
            [1 for _ in range(self._tilemap_size[0])]
            for _ in range(self._tilemap_size[1]) if SETUP_PATHFINDING
        ]

        self._map_objects = MapObjects(self._tilemap)

        self.player_spawnpoint = None
        self.player_entrances = {}

        self.npcs = []
        self.animals = []

        self._setup_layers()

        if SETUP_PATHFINDING:
            AIData.update(self._pf_matrix, self.player)

            if ENABLE_NPCS:
                self._setup_emote_interactions()

    def _add_pf_matrix_collision(
            self, pos: tuple[float, float], size: tuple[float, float]
    ):
        """
        Add a collision rect to the pathfinding matrix at the given position.
        The given position will be the topleft corner of the rectangle.
        The values given to this method should equal to the values as defined
        in Tiled (scaled up by TILE_SIZE, not scaled up by SCALE_FACTOR)
        :param pos: position of collision rect (x, y) (rounded-down)
        :param size: size of collision rect (width, height) (rounded-up)
        """
        tile_x = int(pos[0] / TILE_SIZE)
        tile_y = int(pos[1] / TILE_SIZE)
        tile_w = math.ceil((pos[0] + size[0]) / TILE_SIZE) - tile_x
        tile_h = math.ceil((pos[1] + size[1]) / TILE_SIZE) - tile_y

        for w in range(tile_w):
            for h in range(tile_h):
                try:
                    self._pf_matrix[tile_y + h][tile_x + w] = 0
                except IndexError as e:
                    print(f"An error occurred during GameMap setup: {e}")

    # region tile layer setup methods
    def _setup_base_tile(
            self,
            pos: tuple[int, int],
            surf: pygame.Surface,
            layer: Layer,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group
    ):
        """
        Create a new Sprite and add it to the given groups
        :param pos: Position of the Sprite (x, y)
        :param surf: Surface that will be scaled up by SCALE_FACTOR and serve
                     as image for the Sprite
        :param layer: z-Layer on which the Sprite should be displayed
        :param groups: Groups the Sprite should be added to
        """
        image = pygame.transform.scale_by(surf, SCALE_FACTOR)
        Sprite(pos, image, z=layer).add(groups)

    def _setup_collideable_tile(
            self,
            pos: tuple[int, int],
            surf: pygame.Surface,
            layer: Layer,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group
    ):
        """
        Set up a base tile, and add it as collideable Tile to the pathfinding
        matrix
        """
        self._setup_base_tile(pos, surf, layer, groups)

        if SETUP_PATHFINDING:
            self._add_pf_matrix_collision(
                pos,
                (int(surf.width / SCALED_TILE_SIZE),
                 int(surf.height / SCALED_TILE_SIZE))
            )

    def _setup_water_tile(
            self,
            pos: tuple[int, int],
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group
    ):
        """
        Create a new AnimatedSprite and add it to the given groups.
        This Sprite will be animated as Water and displayed on Layer.WATER
        :param pos: Position of Sprite (x, y)
        :param groups: Groups the Sprite should be added to
        """
        image = self.frames['level']['animations']['water']
        AnimatedSprite(pos, image, z=Layer.WATER).add(groups)
    # endregion

    # region object layer setup methods
    def _setup_base_object(
            self,
            pos: tuple[int, int],
            obj: TiledObject,
            layer: Layer,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
            name: str = None
    ):
        """
        Create a new rectangular hitbox and add it to the given groups.
        :param pos: Position of the hitbox Sprite (x, y)
        :param obj: TiledObject from which the hitbox should be created
        :param layer: z-Layer on which the Sprite should be displayed
                      TODO: Should likely be removed / reworked since hitboxes
                       should not be displayed at all
        :param groups: Groups the Sprite should be added to
        :param name: [Optional] name of the Sprite
        """
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, z=layer, name=name).add(groups)

    def _setup_collision_rect(
            self,
            pos: tuple[int, int],
            obj: TiledObject,
            layer: Layer,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
            name: str = None
    ):
        """
        Set up a base object and add it as collideable object to the
        pathfinding matrix
        """
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, z=layer, name=name).add(groups)

        if SETUP_PATHFINDING:
            self._add_pf_matrix_collision(
                (obj.x, obj.y), (obj.width, obj.height)
            )

    def _setup_collideable_object(
            self,
            pos: tuple[int, int],
            obj: TiledObject,
            layer: Layer,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group
    ):
        """
        Create a new collideable Sprite from the given TiledObject.
        If this map's MapObjects instance doesn't contain this object's GID,
        this method will raise an exception
        """
        CollideableMapObject(
            pos, self._map_objects[obj.gid], z=layer
        ).add(groups)

        if SETUP_PATHFINDING:
            self._add_pf_matrix_collision(
                (obj.x, obj.y), (obj.width, obj.height)
            )

    def _setup_tree_object(
            self,
            pos: tuple[int, int],
            obj: TiledObject,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
    ):
        """
        Create a new collideable Sprite from the given TiledObject.
        This Sprite will be created from the Tree class and will take the apple
        and stump assets from self.frames
        :param pos: Position of Sprite (x, y)
        :param obj: TiledObject to create the Tree from
                    (the obj.image will be used as Tree image)
        :param groups: Groups the Sprite should be added to
        """
        apple_frames = self.frames['level']['objects']['apple']
        stump_frames = self.frames['level']['objects']['stump']

        Tree(pos, self._map_objects[obj.gid],
             groups,
             obj.name, apple_frames, stump_frames)

        if SETUP_PATHFINDING:
            self._add_pf_matrix_collision(
                (obj.x, obj.y), (obj.width, obj.height)
            )

    def _setup_player_point(
            self,
            pos: tuple[int, int],
            obj: TiledObject
    ):
        """
        Add a new Player entrance / spawn point.
        The type of the point will be retrieved from the object's name.

        The default spawnpoint should be named "spawnpoint", and teleport
        destination points should be named "from " + map name (without .tmx),
        e.g. a teleport point used when teleporting from forest should be named
        "from forest". Teleport origins should be defined as rectangular
        objects that teleport the player when colliding with them. They should
        be named "to " + map name (without .tmx), e.g. a teleport point that
        will be used when teleporting to farm_new should be named
        "to farm_new".

        :param pos: Position of the point
        :param obj: TiledObject to create the point from
        """
        name = obj.name
        if name == "spawnpoint":
            if self.player_spawnpoint:
                print("WARNING: Multiple spawnpoints found")
            self.player_spawnpoint = pos
        else:
            name = name.split(" ")
            if len(name) == 2:
                point_type = name[0]
                point_map = name[1]
                if point_type == "from":
                    self.player_entrances[point_map] = pos
                elif point_type == "to":
                    teleport_hitbox = pygame.Surface(
                        (obj.width * SCALE_FACTOR,
                         obj.height * SCALE_FACTOR)
                    )
                    Sprite(
                        (obj.x * SCALE_FACTOR,
                         obj.y * SCALE_FACTOR),
                        teleport_hitbox,
                        name=point_map
                    ).add(self.map_exits)
                else:
                    print(
                        f"WARNING: Invalid player point {name}"
                    )
            else:
                print(f"WARNING: Invalid player point {name}")

    def _setup_npc(
            self,
            pos: tuple[int, int]
    ):
        """
        Creates a new NPC sprite at the given position
        """
        return NPC(
            pos=pos,
            assets=ENTITY_ASSETS.RABBIT,
            groups=(self.all_sprites, self.collision_sprites),
            collision_sprites=self.collision_sprites,
            apply_tool=self.apply_tool,
            soil_layer=self.soil_layer,
            emote_manager=self.npc_emote_manager,
        )

    def _setup_animal(
            self,
            pos: tuple[int, int],
            obj: TiledObject
    ):
        """
        Creates a new Animal sprite at the given position.
        The animal type is determined by the object name, objects named
        "Chicken" will create Chickens, objects that are named "Cow" will
        create Cows.
        """
        if obj.name == "Chicken":
            return Chicken(
                pos=pos,
                assets=ENTITY_ASSETS.CHICKEN,
                groups=(self.all_sprites, self.collision_sprites),
                collision_sprites=self.collision_sprites,
            )
        elif obj.name == "Cow":
            return Cow(
                pos=pos,
                assets=ENTITY_ASSETS.COW,
                groups=(self.all_sprites, self.collision_sprites),
                collision_sprites=self.collision_sprites,
            )
        else:
            print(f"Malformed animal object name \"{obj.name}\" in tilemap")
    # endregion

    def _setup_layers(self):
        """
        Iterates over all map layers, updates the GameMap state and creates
        all Sprites for the map.
        """
        for tilemap_layer in self._tilemap.layers:
            if isinstance(tilemap_layer, TiledTileLayer):
                # create soil layer
                if tilemap_layer.name == "Farmable":
                    self.soil_layer.create_soil_tiles(tilemap_layer)
                    continue
                elif tilemap_layer.name == "Fence":
                    # TODO: Convert the Fence layer to an object layer, or add
                    #  tiles of the Fencer layer to MapObjects to allow for
                    #  smaller hitboxes
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, image: self._setup_collideable_tile(
                            pos, image, Layer.MAIN,
                            (self.all_sprites, self.collision_sprites,)
                        )
                    )
                    continue

                # create visible tile layers
                # set layer if defined in the TileLayer properties
                layer = tilemap_layer.properties.get("layer")
                if layer:
                    try:
                        layer = Layer[layer]
                    except KeyError:
                        print(
                            f"WARNING: Layer {layer} does not exist\n"
                            f"Tiles from the TileLayer {tilemap_layer} "
                            f"will be rendered on GROUND instead"
                        )

                if layer is None:
                    layer = Layer.GROUND

                if layer == Layer.WATER:
                    # tiles on the WATER layer will always be created as water
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, _: self._setup_water_tile(
                            pos, self.all_sprites
                        )
                    )
                elif layer == Layer.BORDER:
                    # tiles on the BORDER layer will always be collideable
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, image: self._setup_collideable_tile(
                            pos, image, layer,
                            (self.all_sprites, self.collision_sprites,)
                        )
                    )
                else:
                    # decorative and ground tiles will be created as base tile
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, image: self._setup_base_tile(
                            pos, image, layer,
                            self.all_sprites
                        )
                    )

            elif isinstance(tilemap_layer, TiledObjectGroup):
                if tilemap_layer.name == "Interactions":
                    _setup_object_layer(
                        tilemap_layer,
                        lambda pos, obj: self._setup_base_object(
                            pos, obj, Layer.MAIN, self.interaction_sprites,
                            name=obj.name
                        )
                    )
                elif tilemap_layer.name == "Collisions":
                    _setup_object_layer(
                        tilemap_layer,
                        lambda pos, obj: self._setup_collision_rect(
                            pos, obj, Layer.MAIN, self.collision_sprites
                        )
                    )
                elif tilemap_layer.name == "Trees":
                    _setup_object_layer(
                        tilemap_layer,
                        lambda pos, obj: self._setup_tree_object(
                            pos, obj,
                            (self.all_sprites, self.collision_sprites,
                             self.tree_sprites)
                        )
                    )
                elif tilemap_layer.name == "Player":
                    _setup_object_layer(
                        tilemap_layer,
                        lambda pos, obj: self._setup_player_point(pos, obj)
                    )

                    if (not self.player_entrances and
                            not self.player_spawnpoint):
                        raise InvalidMapException(
                            "No Player entrance point has been found in the "
                            "map's Player layer"
                        )
                elif tilemap_layer.name == "NPCs":
                    if ENABLE_NPCS:
                        self.npcs = _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_npc(pos)
                        )
                    else:
                        continue
                elif tilemap_layer.name == "Animals":
                    if TEST_ANIMALS:
                        self.animals = _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_animal(pos, obj)
                        )
                    else:
                        continue
                else:
                    # decorative objects will be created as collideable object
                    _setup_object_layer(
                        tilemap_layer,
                        lambda pos, obj: self._setup_collideable_object(
                            pos, obj, Layer.MAIN,
                            (self.all_sprites, self.collision_sprites)
                        )
                    )

            else:
                # This should be the case when an Image or Group layer is found
                print(f"WARNING: Support for {type(tilemap_layer)} layers is "
                      f"not (yet) implemented! Layer {tilemap_layer.name} "
                      f"will be skipped")

    def _setup_emote_interactions(self):
        self.player_emote_manager.reset()

        @self.player_emote_manager.on_show_emote
        def on_show_emote(emote: str):
            if self.player.focused_entity:
                npc = self.player.focused_entity
                npc.abort_path()

                self.npc_emote_manager.show_emote(npc, emote)

        @self.player_emote_manager.on_emote_wheel_opened
        def on_emote_wheel_opened():
            player_pos = self.player.rect.center
            distance_to_player = 5 * SCALED_TILE_SIZE
            npc_to_focus = None
            for npc in self.npcs:
                current_distance = (
                    (player_pos[0] - npc.rect.center[0]) ** 2 +
                    (player_pos[1] - npc.rect.center[1]) ** 2
                ) ** .5
                if current_distance < distance_to_player:
                    distance_to_player = current_distance
                    npc_to_focus = npc
            if npc_to_focus:
                self.player.focus_entity(npc_to_focus)

        @self.player_emote_manager.on_emote_wheel_closed
        def on_emote_wheel_closed():
            self.player.unfocus_entity()

    def get_size(self):
        return self._tilemap_scaled_size
