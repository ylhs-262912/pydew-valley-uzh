from collections.abc import Callable
from typing import Self, Any

import pygame
from random import choice

from pytmx import TiledMap

from src.enums import SeedType, InventoryResource, FarmingTool
from src.support import tile_to_screen
from src.sprites.base import Sprite
from src.sprites.plant import Plant
from src.settings import LAYERS, SCALED_TILE_SIZE


class Tile(Sprite):
    pos: tuple[int, int]

    farmable: bool
    hoed: bool
    plant: Plant | None
    planted: bool
    watered: bool

    pf_weight: float

    def __init__(
            self, pos: tuple[int, int], group: tuple[pygame.sprite.Group, ...]
    ):
        self._callback = None

        surf = pygame.Surface(
            (SCALED_TILE_SIZE, SCALED_TILE_SIZE), pygame.SRCALPHA
        )

        super().__init__(tile_to_screen(pos), surf, group, LAYERS["soil"])

        self.pos = pos
        self.farmable = False
        self.hoed = False
        self.plant = None
        self.plant_harvestable = False
        self.watered = False
        self.pf_weight = 0

    @property
    def planted(self):
        return self.plant is not None

    def grow_plant(self):
        if self.planted:
            self.plant.grow()
            if self.plant.age == self.plant.max_age:
                self.plant_harvestable = True

    def register_callback(self, callback: Callable[[Self, str, Any], None]):
        self._callback = callback

    def __setattr__(self, key, value):
        try:
            self._callback(self, key, value)
        except (AttributeError, TypeError):
            pass

        super().__setattr__(key, value)


class SoilLayer:
    all_sprites: pygame.sprite.Group
    level_frames: dict

    soil_sprites: pygame.sprite.Group
    water_sprites: pygame.sprite.Group
    plant_sprites: pygame.sprite.Group

    tiles: dict[tuple[int, int], Tile]
    neighbor_directions: list[tuple[int, int]]

    raining: bool

    def __init__(
            self, all_sprites: pygame.sprite.Group,
            tmx_map: TiledMap, frames: dict
    ):
        self.all_sprites = all_sprites
        self.level_frames = frames

        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.tiles = {}

        self._untilled_tiles = set(self.tiles.keys())
        self._unplanted_tiles = set()
        self._unwatered_tiles = set()
        self.planted_types = {
            i: 0 for i in SeedType
        }

        self.create_soil_tiles(tmx_map)

        self.neighbor_directions = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]

        self.raining = False

    @property
    def raining(self) -> bool:
        return self._raining

    @raining.setter
    def raining(self, value: bool):
        self._raining = value
        if self._raining:
            self.water_all()

    @property
    def untilled_tiles(self):
        return self._untilled_tiles

    @property
    def unplanted_tiles(self):
        return self._unplanted_tiles

    @property
    def unwatered_tiles(self):
        return self._unwatered_tiles

    def on_tile_update(self, tile: Tile, attr_name: str, attr_value: Any):
        match attr_name:
            case "farmable":
                if attr_value:
                    if not tile.hoed:
                        self._untilled_tiles.add(tile.pos)
                else:
                    self._untilled_tiles.discard(tile.pos)
            case "hoed":
                if attr_value:
                    self._untilled_tiles.discard(tile.pos)
                    if not tile.planted:
                        self._unplanted_tiles.add(tile.pos)
                else:
                    self._unplanted_tiles.discard(tile.pos)
                    if tile.farmable:
                        self.untilled_tiles.add(tile.pos)
            case "plant":
                if attr_value:
                    self.planted_types[attr_value.seed_type] += 1

                    self._unplanted_tiles.discard(tile.pos)
                    if not tile.watered:
                        self._unwatered_tiles.add(tile.pos)
                else:
                    if tile.plant:
                        self.planted_types[tile.plant.seed_type] -= 1

                    self._unwatered_tiles.discard(tile.pos)
                    if tile.hoed:
                        self._unplanted_tiles.add(tile.pos)
            case "watered":
                if attr_value:
                    self._unwatered_tiles.discard(tile.pos)
                else:
                    if tile.planted:
                        self._unwatered_tiles.add(tile.pos)

    def create_soil_tiles(self, tmx_map):
        farmable_layer = tmx_map.get_layer_by_name("Farmable")
        for x, y, _ in farmable_layer.tiles():
            tile = Tile((x, y), (self.all_sprites, self.soil_sprites))
            tile.register_callback(self.on_tile_update)
            tile.farmable = True
            self.tiles[(x, y)] = tile

    def update_tile_image(self, tile, pos):
        for dx, dy in self.neighbor_directions:
            neighbor = self.tiles.get((pos[0] + dx, pos[1] + dy))
            if neighbor:
                neighbor_pos = (pos[0] + dx, pos[1] + dy)
                neighbor_type = self.determine_tile_type(neighbor_pos)
                if neighbor.hoed:
                    neighbor.image = self.level_frames["soil"][neighbor_type]
                    neighbor.pf_weight = 0
                else:
                    neighbor.pf_weight = int(neighbor_type != "o")

        tile_type = self.determine_tile_type(pos)
        if tile.hoed:
            tile.image = self.level_frames["soil"][tile_type]
            tile.pf_weight = 0
        else:
            tile.pf_weight = int(tile_type != "o")

    def hoe(self, pos) -> bool:
        """:return: Whether the tile was successfully hoed or not"""
        tile = self.tiles.get(pos)
        if tile and tile.farmable and not tile.hoed:
            tile.hoed = True
            self.update_tile_image(tile, pos)
            return True
        return False

    def water(self, pos):
        """:return: Whether the tile was successfully watered or not"""
        tile = self.tiles.get(pos)
        if tile and tile.hoed and not tile.watered:
            tile.watered = True

            water_frames = list(self.level_frames["soil water"].values())
            water_frame = choice(water_frames)
            Sprite(
                tile_to_screen(pos),
                water_frame,
                (self.all_sprites, self.water_sprites),
                LAYERS["soil water"],
            )
            return True

        return False

    def water_all(self):
        for pos, tile in self.tiles.items():
            if tile.hoed:
                self.water(pos)
                self.update_tile_image(tile, pos)

    def plant(
            self, pos, seed,
            remove_resource: Callable[[InventoryResource, int], bool]
    ):
        """:return: Whether the tile was successfully planted or not"""
        tile = self.tiles.get(pos)
        seed_resource = FarmingTool.as_inventory_resource(seed)
        seed_type = SeedType.from_farming_tool(seed)

        if tile and tile.hoed and not tile.planted:
            if not remove_resource(seed_resource, 1):
                return False

            tile.planted = True
            seed_name = seed_type.as_plant_name()
            frames = self.level_frames[seed_name]
            groups = (self.all_sprites, self.plant_sprites)
            tile.plant = Plant(seed_type, groups, tile, frames)
            return True

        return False

    def harvest(
            self, pos, add_resource: Callable[[InventoryResource, int], None],
            create_particle: Callable[[pygame.sprite.Sprite], None]
    ) -> bool:
        """:return: Whether the tile was successfully harvested or not"""

        tile = self.tiles.get(pos)
        if tile and tile.plant.harvestable:
            # add resource
            resource = SeedType.as_nonseed_ir(tile.plant.seed_type)
            quantity = 3

            add_resource(resource, quantity)

            # remove plant
            tile.plant.kill()
            create_particle(tile.plant)
            tile.plant = None
            return True

        return False

    def update(self):
        for tile in self.tiles.values():
            if tile.plant:
                tile.plant.grow()
            tile.watered = False
            for sprite in self.water_sprites:
                sprite.kill()

    def determine_tile_type(self, pos):
        x, y = pos
        tile_above = self.tiles.get((x, y - 1))
        tile_below = self.tiles.get((x, y + 1))
        tile_right = self.tiles.get((x + 1, y))
        tile_left = self.tiles.get((x - 1, y))

        hoed_above = tile_above.hoed if tile_above else False
        hoed_below = tile_below.hoed if tile_below else False
        hoed_right = tile_right.hoed if tile_right else False
        hoed_left = tile_left.hoed if tile_left else False

        if all((hoed_above, hoed_right, hoed_below, hoed_left)):
            return "x"
        if hoed_left and not any((hoed_above, hoed_right, hoed_below)):
            return "r"
        if hoed_right and not any((hoed_above, hoed_left, hoed_below)):
            return "l"
        if hoed_right and hoed_left and not any((hoed_above, hoed_below)):
            return "lr"
        if hoed_above and not any((hoed_right, hoed_left, hoed_below)):
            return "b"
        if hoed_below and not any((hoed_right, hoed_left, hoed_above)):
            return "t"
        if hoed_below and hoed_above and not any((hoed_right, hoed_left)):
            return "tb"
        if hoed_left and hoed_below and not any((hoed_above, hoed_right)):
            return "tr"
        if hoed_right and hoed_below and not any((hoed_above, hoed_left)):
            return "tl"
        if hoed_left and hoed_above and not any((hoed_below, hoed_right)):
            return "br"
        if hoed_right and hoed_above and not any((hoed_below, hoed_left)):
            return "bl"
        if all((hoed_above, hoed_below, hoed_right)) and not hoed_left:
            return "tbr"
        if all((hoed_above, hoed_below, hoed_left)) and not hoed_right:
            return "tbl"
        if all((hoed_left, hoed_right, hoed_above)) and not hoed_below:
            return "lrb"
        if all((hoed_left, hoed_right, hoed_below)) and not hoed_above:
            return "lrt"
        return "o"
