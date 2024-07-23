from collections.abc import Callable

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
    planted: bool
    watered: bool

    plant: Plant | None

    def __init__(
            self, pos: tuple[int, int], group: tuple[pygame.sprite.Group, ...]
    ):
        surf = pygame.Surface(
            (SCALED_TILE_SIZE, SCALED_TILE_SIZE), pygame.SRCALPHA
        )

        super().__init__(tile_to_screen(pos), surf, group, LAYERS["soil"])

        self.pos = pos
        self.hoed = False
        self.watered = False
        self.planted = False
        self.farmable = False
        self.plant = None


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

    def create_soil_tiles(self, tmx_map):
        farmable_layer = tmx_map.get_layer_by_name("Farmable")
        for x, y, _ in farmable_layer.tiles():
            tile = Tile((x, y), (self.all_sprites, self.soil_sprites))
            tile.farmable = True
            self.tiles[(x, y)] = tile

    def update_tile_image(self, tile, pos):
        for dx, dy in self.neighbor_directions:
            neighbor = self.tiles.get((pos[0] + dx, pos[1] + dy))
            if neighbor and neighbor.hoed:
                neighbor_pos = (pos[0] + dx, pos[1] + dy)
                neighbor_type = self.determine_tile_type(neighbor_pos)
                neighbor.image = self.level_frames["soil"][neighbor_type]

        tile_type = self.determine_tile_type(pos)
        tile.image = self.level_frames["soil"][tile_type]

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

    def update(self):
        for tile in self.tiles.values():
            if tile.plant:
                tile.plant.grow()
            tile.watered = False
            for sprite in self.water_sprites:
                sprite.kill()

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
        plant = tile.plant
        if tile and plant.harvestable:
            # add resource
            resource = SeedType.as_nonseed_ir(plant.seed_type)
            quantity = 3

            add_resource(resource, quantity)

            tile.planted = False

            # remove plant
            plant.kill()
            create_particle(plant)
            return True

        return False

    def get_untilled_tiles(self) -> dict[tuple[int, int], Tile]:
        untilled_tiles = {}
        for pos, tile in self.tiles.items():
            if not tile.hoed:
                untilled_tiles[pos] = tile
        return untilled_tiles

    def get_unplanted_tiles(self) -> dict[tuple[int, int], Tile]:
        unplanted_tiles = {}
        for pos, tile in self.tiles.items():
            if not tile.planted:
                unplanted_tiles[pos] = tile
        return unplanted_tiles

    def get_unwatered_tiles(self) -> dict[tuple[int, int], Tile]:
        unwatered_tiles = {}
        for pos, tile in self.tiles.items():
            if not tile.watered:
                unwatered_tiles[pos] = tile
        return unwatered_tiles

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
