import os.path
from dataclasses import dataclass
from xml.etree import ElementTree

import pygame

from src.enums import Tileset
from src.settings import SCALE_FACTOR


@dataclass
class MapObjectType:
    image: pygame.Surface
    hitbox: pygame.Rect


class MapObjects:
    objects: dict[int, MapObjectType]

    def __init__(self, tileset: Tileset):
        self.objects = get_object_hitboxes(tileset.value)


def get_object_hitboxes(path_to_tileset: str) -> dict[int, MapObjectType]:
    """
    Returns a dictionary mapping the IDs of all tiles in a given tileset
    to the first hitbox created with the Tiled Tile Collision Editor.
    If no hitbox is found, it uses the dimensions of the Tile's image.

    This function is currently experimental and has only been tested with rectangular hitboxes.
    It is also currently limited to integer values within the dimensions of the hitbox.

    :return: Dictionary mapping the IDs of all tiles in a given tileset to its hitbox (x, y, width, height)
    """
    tree = ElementTree.parse(path_to_tileset)
    root = tree.getroot()

    objects = {}
    try:
        for child in root:
            obj = {
                "id": None,
                "hitbox": None,
                "image": None
            }
            if child.tag == "tile":
                obj["id"] = child.attrib.get("id")

                image = child.find("image")
                if image is None:
                    raise Exception(f"Malformed tileset {path_to_tileset}\n")

                obj["image"] = pygame.image.load(
                    os.path.join(os.path.dirname(path_to_tileset),
                                 image.attrib.get("source"))
                ).convert_alpha()

                objectgroup = child.find("objectgroup")
                if objectgroup is not None:
                    hitbox = objectgroup.find("object")
                    if hitbox is not None:
                        obj["hitbox"] = pygame.Rect(
                            int(hitbox.attrib.get("x")) * SCALE_FACTOR,
                            int(hitbox.attrib.get("y")) * SCALE_FACTOR,
                            int(hitbox.attrib.get("width")) * SCALE_FACTOR,
                            int(hitbox.attrib.get("height")) * SCALE_FACTOR
                        )
                else:
                    obj["hitbox"] = pygame.Rect(
                        0, 0,
                        int(image.attrib.get("width")) * SCALE_FACTOR,
                        int(image.attrib.get("height")) * SCALE_FACTOR
                    )
                if obj["id"] is not None:
                    objects[int(obj["id"])] = MapObjectType(
                        image=obj["image"],
                        hitbox=obj["hitbox"]
                    )
                else:
                    raise Exception(f"Malformed tileset {path_to_tileset}\n")
    except KeyError as e:
        raise Exception(f"Malformed tileset {path_to_tileset}\n") from e
    return objects
