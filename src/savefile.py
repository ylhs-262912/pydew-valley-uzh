import json
from .enums import InventoryResource, FarmingTool
from .support import resource_path
from jsmin import jsmin


class SaveFileEncoder(json.JSONEncoder):
    def default(self, o):
        # Overriding this so we get readable save files.
        if (isinstance(o, dict) and any(map(InventoryResource.__instancecheck__, o.values())) or
                any(map(FarmingTool.__instancecheck__, o.keys()))):
            ret = {}
            for k in o:
                # Replacing enum values by strings, to ensure the save files can be more easily read and checked.
                # The getattr call ensures that only enum classes will get serialised differently.
                ret[k] = getattr(o[k], "as_serialised_string", lambda: o[k])
            return ret
        return super().default(o)


CONVERT_TO_FT = "__FarmingTool__"
CONVERT_TO_IR = "__InventoryResource__"


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


def load_savefile():
    with open(resource_path("data/save.json"), "r") as file:
        return json.loads(jsmin(file.read()), object_hook=decoder_object_hook)
