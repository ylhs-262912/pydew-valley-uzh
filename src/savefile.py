import json
from .settings import InventoryResource


class SaveFileEncoder(json.JSONEncoder):
    def default(self, o):
        # Overriding this so we get readable save files.
        if isinstance(o, dict) and all(map(InventoryResource.__instancecheck__, o.keys())):
            ret = {}
            for k in o:
                # Replacing enum values by strings, to ensure the save files can be more easily read and checked.
                ret[k.as_serialised_string()] = o[k]
            return ret
        return super().default(o)
