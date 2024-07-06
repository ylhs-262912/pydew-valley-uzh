import json
from .enums import InventoryResource, FarmingTool
from .support import resource_path
from jsmin import jsmin

CONVERT_TO_FT = "__FarmingTool__"
CONVERT_TO_IR = "__InventoryResource__"


class SaveFileEncoder(json.JSONEncoder):
    def default(self, o):
        # Overriding this so we get readable save files.
        if (isinstance(o, dict) and any(map(InventoryResource.__instancecheck__, o.values())) or
                any(map(FarmingTool.__instancecheck__, o.keys()))):
            ret = {}
            _convert_to_ft = []
            _convert_to_ir = []
            for k in o:
                # Replacing enum values by strings, to ensure the save files can be more easily read and checked.
                # The getattr call ensures that only enum classes will get serialised differently.
                if isinstance(o[k], InventoryResource):
                    _convert_to_ir.append(k)
                if isinstance(o[k], FarmingTool):
                    _convert_to_ft.append(k)
                ret[k] = getattr(o[k], "as_serialised_string", lambda: o[k])()
            if _convert_to_ft:
                ret[CONVERT_TO_FT] = _convert_to_ft
            if _convert_to_ir:
                ret[CONVERT_TO_IR] = _convert_to_ir
            return ret
        return super().default(o)


def as_farmingtool(o: dict):
    if CONVERT_TO_FT in o:
        ret = o.copy()
        del ret[CONVERT_TO_FT]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_FT]:
                ret[k] = FarmingTool.from_serialised_string(o[k])
        return ret
    return o


def as_inventoryresource(o: dict):
    if CONVERT_TO_IR in o:
        ret = o.copy()
        del ret[CONVERT_TO_IR]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_IR]:
                ret[InventoryResource.from_serialised_string(k)] = o[k]
        return ret
    return o


def decoder_object_hook(o):
    processed = as_farmingtool(o)
    processed = as_inventoryresource(processed)
    return processed


def save(current_tool: FarmingTool, current_seed: FarmingTool, inventory: dict[InventoryResource, int]):
    with open(resource_path("data/save.json"), "w") as file:
        obj_to_dump = {
            "current_tool": current_tool,
            "current_seed": current_seed,
            "inventory": inventory
        }
        json.dump(obj_to_dump, file, cls=SaveFileEncoder)


def load_savefile():
    with open(resource_path("data/save.json"), "r") as file:
        return json.loads(jsmin(file.read()), object_hook=decoder_object_hook)
