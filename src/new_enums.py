from enum import Enum, IntEnum, auto


class PlayerState(IntEnum):         # useless
    IDLE = 0
    WALK = 1


class ItemToUse(IntEnum):         # useless
    REGULAR_TOOL = 0
    SEED = 1


class GameState(IntEnum):
    MAIN_MENU = 0
    LEVEL = 1
    PAUSE = 2
    SETTINGS = 3
    SHOP = 4
    EXIT = 5
    GAME_OVER = 6
    WIN = 7
    CREDITS = 8


class InventoryResource(Enum):
    WOOD = auto()
    APPLE = auto()
    CORN = auto()
    TOMATO = auto()
    CORN_SEED = auto()
    TOMATO_SEED = auto()


ITEM_WORTHS = {
    InventoryResource.WOOD: 8,
    InventoryResource.APPLE: 4,
    InventoryResource.CORN: 20,
    InventoryResource.TOMATO: 40,
    InventoryResource.CORN_SEED: 4,
    InventoryResource.TOMATO_SEED: 5,
}


def get_item_worth(item: InventoryResource) -> int:
    return ITEM_WORTHS[item]


def is_inventory_seed(item: InventoryResource) -> bool:
    return item in {InventoryResource.CORN_SEED, InventoryResource.TOMATO_SEED}


class FarmingTool(Enum):
    NONE = auto()
    AXE = auto()
    HOE = auto()
    WATERING_CAN = auto()
    CORN_SEED = auto()
    TOMATO_SEED = auto()


TOOL_TO_RESOURCE = {
    FarmingTool.CORN_SEED: InventoryResource.CORN,
    FarmingTool.TOMATO_SEED: InventoryResource.TOMATO
}

SWINGING_TOOLS = {FarmingTool.HOE, FarmingTool.AXE}


def is_swinging_tool(tool: FarmingTool) -> bool:
    return tool in SWINGING_TOOLS


def is_farming_seed(tool: FarmingTool) -> bool:
    return tool in {FarmingTool.CORN_SEED, FarmingTool.TOMATO_SEED}


def convert_to_inventory_resource(tool: FarmingTool) -> InventoryResource:
    return TOOL_TO_RESOURCE.get(tool, tool)


class SeedType(IntEnum):
    CORN = 0
    TOMATO = 1


SEED_TO_TOOL = {
    SeedType.CORN: FarmingTool.CORN_SEED,
    SeedType.TOMATO: FarmingTool.TOMATO_SEED
}

SEED_TO_INVENTORY_RESOURCE = {
    SeedType.CORN: InventoryResource.CORN_SEED,
    SeedType.TOMATO: InventoryResource.TOMATO_SEED
}

SEED_TO_NON_SEED_RESOURCE = {
    SeedType.CORN: InventoryResource.CORN,
    SeedType.TOMATO: InventoryResource.TOMATO
}


def seed_from_farming_tool(tool: FarmingTool) -> SeedType:
    return SeedType(list(SEED_TO_TOOL.values()).index(tool))


def seed_from_inventory_resource(resource: InventoryResource) -> SeedType:
    return SeedType(list(SEED_TO_INVENTORY_RESOURCE.values()).index(resource))


def convert_to_seed_inventory_resource(seed: SeedType) -> InventoryResource:
    return SEED_TO_INVENTORY_RESOURCE[seed]


def convert_to_non_seed_inventory_resource(seed: SeedType) -> InventoryResource:
    return SEED_TO_NON_SEED_RESOURCE[seed]


def get_plant_name(seed: SeedType) -> str:
    return SEED_TO_TOOL[seed].name.replace('_SEED', '').lower()