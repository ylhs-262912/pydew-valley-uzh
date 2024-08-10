import json

from jsmin import jsmin

from src.enums import FarmingTool, InventoryResource, SeedType, StudyGroup
from src.savefile.tile_info import PlantInfo, TileInfo
from src.settings import GogglesStatus
from src.support import resource_path

CONVERT_TO_FT = "__FarmingTool__"
CONVERT_TO_IR = "__InventoryResource__"


def _as_farmingtool(o: dict):
    if CONVERT_TO_FT in o:
        ret = o.copy()
        del ret[CONVERT_TO_FT]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_FT]:
                ret[k] = FarmingTool.from_serialised_string(o[k])
        return ret
    return o


def _as_inventoryresource(o: dict):
    if CONVERT_TO_IR in o:
        ret = o.copy()
        del ret[CONVERT_TO_IR]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_IR]:
                ret[InventoryResource.from_serialised_string(k)] = o[k]
        return ret
    return o


def _extract_group(o: dict):
    if "group" in o:
        ret = o.copy()
        ret["group"] = StudyGroup(ret["group"])
        return ret
    return o


def _extract_tile_info(o: dict):
    if "soil_data" in o:
        ret = o.copy()
        orig_soil_data = ret["soil_data"]
        converted_data = {}
        for pos, info in orig_soil_data.items():
            plant_info_orig = info.get("plant_info")
            if plant_info_orig is not None:
                new_plant_info = PlantInfo(
                    SeedType(plant_info_orig["plant_type"], plant_info_orig["age"])
                )
            else:
                new_plant_info = None
            is_hoed = info.get("hoed", False)
            is_watered = info.get("watered", False)
            converted_data[pos] = TileInfo(is_hoed, is_watered, pos, new_plant_info)
        ret["soil_data"] = converted_data
        return ret
    return o


def _decoder_object_hook(o):
    processed = _as_farmingtool(o)
    processed = _as_inventoryresource(processed)
    processed = _extract_group(processed)
    processed = _extract_tile_info(processed)
    return processed


def save(
    current_tool: FarmingTool,
    current_seed: FarmingTool,
    money: int,
    inventory: dict[InventoryResource, int],
    group: StudyGroup,
    has_goggles: GogglesStatus,
):
    with open(resource_path("data/save.json"), "w") as file:
        serialised_inventory = {
            k.as_serialised_string(): inventory[k] for k in inventory
        }
        keys_to_convert = list(serialised_inventory.keys())
        serialised_inventory[CONVERT_TO_IR] = keys_to_convert
        obj_to_dump = {
            CONVERT_TO_FT: ["current_tool", "current_seed"],
            "money": money,
            "current_tool": current_tool.as_serialised_string(),
            "current_seed": current_seed.as_serialised_string(),
            "group": group.value,
            "goggles_status": has_goggles,
            "inventory": serialised_inventory,
        }
        json.dump(obj_to_dump, file, indent=2)


def load_savefile():
    with open(resource_path("data/save.json"), "r") as file:
        return json.loads(jsmin(file.read()), object_hook=_decoder_object_hook)
