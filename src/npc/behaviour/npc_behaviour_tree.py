from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from src.enums import FarmingTool, ItemToUse, SeedType
from src.npc.behaviour.ai_behaviour_tree_base import (
    Context, Selector, Sequence, Condition, Action, BehaviourTreeBase
)
from src.npc.bases.npc_base import NPCBase
from src.settings import SCALED_TILE_SIZE
from src.support import near_tiles


@dataclass
class NPCBehaviourTreeContext(Context):
    npc: NPCBase


# TODO: NPCs can not harvest fully grown crops on their own yet
class NPCBehaviourTree(BehaviourTreeBase):
    tree = None

    @classmethod
    def init(cls):
        cls.tree = Selector([
            Sequence([
                Condition(cls.will_farm),
                Selector([
                    Sequence([
                        Condition(cls.will_create_new_farmland),
                        Action(cls.create_new_farmland)
                    ]),
                    Sequence([
                        Condition(cls.will_plant_tilled_farmland),
                        Action(cls.plant_adjacent_or_random_seed)
                    ]),
                    Action(cls.water_farmland)
                ])
            ]),
            Action(cls.wander)
        ])

    @staticmethod
    def will_farm(context: NPCBehaviourTreeContext) -> bool:
        """
        1 in 3 chance to go farming instead of wandering around
        :return: 1/3 true | 2/3 false
        """
        return random.randint(0, 2) == 0

    @staticmethod
    def will_create_new_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        :return: True: untilled farmland available AND
        (all other farmland planted and watered OR 1/3), otherwise False
        """
        soil_layer = context.npc.soil_layer

        if not len(soil_layer.untilled_tiles):
            return False

        unplanted_farmland_available = len(soil_layer.unplanted_tiles)
        unwatered_farmland_available = len(soil_layer.unwatered_tiles)

        return (
                unplanted_farmland_available == 0
                and unwatered_farmland_available == 0
        ) or random.randint(0, 2) == 0

    @staticmethod
    def create_new_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        Finds a random untilled but farmable tile in a radius of 5 around the
        NPC. Will prefer Tiles that are adjacent to already tilled Tiles in 6/7
        of all cases.
        :return: True if such a Tile has been found and the NPC successfully
                 created a path towards it, otherwise False
        """
        if not len(context.npc.soil_layer.untilled_tiles):
            return False

        radius = 5

        # current NPC position on the tilemap
        tile_coord = context.npc.get_tile_pos()

        weighted_coords = []
        coords = []

        for pos in near_tiles(tile_coord, radius):
            if pos in context.npc.soil_layer.untilled_tiles:
                if context.npc.soil_layer.tiles.get(pos).pf_weight:
                    weighted_coords.append(pos)
                else:
                    coords.append(pos)

        w_coords: list[tuple[float, tuple[int, int]]] = []

        for pos in weighted_coords:
            w_coords.append((1 * len(weighted_coords), pos))

        for pos in coords:
            w_coords.append((7 * len(coords), pos))

        order = sorted(
            range(len(w_coords)),
            key=lambda i: random.random() ** (1.0 / w_coords[i][0])
        )

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.HOE
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        for pos in order:
            path_created = NPCBehaviourTree.wander_to_interact(
                context, w_coords[pos][1], on_path_completion
            )
            if path_created:
                return True

        return False

    @staticmethod
    def will_plant_tilled_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        :return: True if unplanted farmland available AND
        (all other farmland watered OR 3/4), otherwise False
        """
        soil_layer = context.npc.soil_layer

        if not len(soil_layer.unplanted_tiles):
            return False

        unwatered_farmland_available = len(soil_layer.unwatered_tiles)

        return unwatered_farmland_available == 0 or random.randint(0, 3) <= 2

    @staticmethod
    def plant_adjacent_or_random_seed(
            context: NPCBehaviourTreeContext
    ) -> bool:
        """
        Finds a random unplanted but tilled tile in a radius of 5 around the
        NPC, makes the NPC walk to and plant a seed on it.
        The seed selected is dependent on the respective amount of planted
        seeds from all seed types, as well as the seed types that have been
        planted on tiles adjacent to the randomly selected tile.
        :return: True if such a Tile has been found and the NPC successfully
                 created a path towards it, otherwise False
        """
        soil_layer = context.npc.soil_layer

        if not len(soil_layer.unplanted_tiles):
            return False

        radius = 5

        tile_coord = context.npc.get_tile_pos()

        def on_path_completion():
            seed_type: FarmingTool | None = None

            # NPCs will only plant a seed from an adjacent tile if every seed
            # type is planted on at least
            # 1/(number of available seed types * 1.5)
            # of all planted tiles
            total_planted = sum(soil_layer.planted_types.values())
            seed_types_count = len(soil_layer.planted_types.keys())

            threshold = total_planted / (seed_types_count * 1.5)

            will_plant_adjacent_seed = (
                not total_planted or
                all([seed_type > threshold
                     for seed_type in soil_layer.planted_types.values()])
            )

            if will_plant_adjacent_seed:
                adjacent_seed_types = set()
                for dx, dy in soil_layer.neighbor_directions:
                    neighbor_pos = (pos[0] + dx, pos[1] + dy)
                    neighbor = soil_layer.tiles.get(neighbor_pos)
                    if neighbor and neighbor.plant:
                        neighbor_seed_type = neighbor.plant.seed_type
                        adjacent_seed_types.add(
                            (soil_layer.planted_types[neighbor_seed_type],
                             neighbor_seed_type.as_farming_tool())
                        )

                # If multiple adjacent seed types are found, the one that has
                # been planted the least is used
                if adjacent_seed_types:
                    seed_type = min(
                        adjacent_seed_types,
                        key=lambda i: i[0]
                    )[1]

            # If no adjacent seed type has been found, the type with that has
            # been planted the least is used
            if not seed_type:
                seed_type = min(
                    SeedType, key=lambda x: soil_layer.planted_types[x]
                ).as_farming_tool()

            context.npc.current_seed = seed_type
            context.npc.seed_index = (context.npc.current_seed.value
                                      - FarmingTool.get_first_seed_id().value)
            context.npc.use_tool(ItemToUse.SEED)

        for pos in near_tiles(tile_coord, radius, shuffle=True):
            if pos in soil_layer.unplanted_tiles:
                path_created = NPCBehaviourTree.wander_to_interact(
                    context, pos, on_path_completion
                )
                if path_created:
                    return True

        return False

    @staticmethod
    def water_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        Finds a random unwatered but planted tile in a radius of 5 around the
        NPC, makes the NPC walk to and water it.
        :return: True if such a Tile has been found and the NPC successfully
                 created a path towards it, otherwise False
        """
        soil_layer = context.npc.soil_layer
        if not len(soil_layer.unwatered_tiles):
            return False

        radius = 5

        tile_coord = context.npc.get_tile_pos()

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.WATERING_CAN
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        for pos in near_tiles(tile_coord, radius):
            if pos in soil_layer.unwatered_tiles:
                path_created = NPCBehaviourTree.wander_to_interact(
                    context, pos, on_path_completion
                )
                if path_created:
                    return True

        return False

    @staticmethod
    def wander_to_interact(context: NPCBehaviourTreeContext,
                           target_position: tuple[int, int],
                           on_path_completion: Callable[[], None]):
        """
        :return: True if path has successfully been created, otherwise False
        """

        if context.npc.create_path_to_tile(target_position):
            if len(context.npc.pf_path) > 1:
                facing = (
                    context.npc.pf_path[-1][0] - context.npc.pf_path[-2][0],
                    context.npc.pf_path[-1][1] - context.npc.pf_path[-2][1]
                )
            else:
                facing = (
                    context.npc.pf_path[-1][0]
                    - context.npc.rect.centerx / SCALED_TILE_SIZE,
                    context.npc.pf_path[-1][1]
                    - context.npc.rect.centery / SCALED_TILE_SIZE
                )

            facing = (facing[0], 0)\
                if abs(facing[0]) > abs(facing[1])\
                else (0, facing[1])

            @context.npc.on_path_completion
            def inner():
                context.npc.direction.update(facing)
                context.npc.get_facing_direction()
                context.npc.direction.update((0, 0))

                on_path_completion()

            return True
        return False

    @staticmethod
    def wander(context: NPCBehaviourTreeContext) -> bool:
        """
        Makes the NPC wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """

        # current NPC position on the tilemap
        tile_coord = context.npc.get_tile_pos()

        for pos in near_tiles(tile_coord, 3, shuffle=True):
            if context.npc.create_path_to_tile(pos):
                return True

        return False
