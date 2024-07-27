import os.path
from dataclasses import dataclass
from xml.etree import ElementTree

import pygame

from src.enums import Tileset
from src.settings import SCALE_FACTOR


@dataclass
class MapObjectType:
    id: int = None

    image: pygame.Surface = None
    hitbox: pygame.FRect = None


class MapObjects:
    objects: dict[int, MapObjectType]

    def __init__(self, *tilesets: Tileset):
        self.objects = {}
        for tileset in tilesets:
            self.objects.update(get_object_hitboxes(tileset))


def _get_obj_hitbox(
        obj: ElementTree.Element, path: str = ""
) -> MapObjectType | None:
    _return_object = MapObjectType()
    if obj.tag == "tile":
        _return_object.id = int(obj.attrib.get("id"))

        image = obj.find("image")
        if image is None or _return_object.id is None:
            return

        _return_object.image = pygame.image.load(
            os.path.join(os.path.dirname(path),
                         image.attrib.get("source"))
        ).convert_alpha()

        objectgroup = obj.find("objectgroup")
        if objectgroup:
            hitbox = objectgroup.find("object")
            if hitbox is not None:
                _return_object.hitbox = pygame.FRect(
                    float(hitbox.attrib.get("x")) * SCALE_FACTOR,
                    float(hitbox.attrib.get("y")) * SCALE_FACTOR,
                    float(hitbox.attrib.get("width")) * SCALE_FACTOR,
                    float(hitbox.attrib.get("height")) * SCALE_FACTOR
                )
        else:
            _return_object.hitbox = pygame.FRect(
                0, 0,
                int(image.attrib.get("width")) * SCALE_FACTOR,
                int(image.attrib.get("height")) * SCALE_FACTOR
            )

        return _return_object
    return


def get_object_hitboxes(path_to_tileset: str) -> dict[int, MapObjectType]:
    """
    Returns a dictionary mapping the IDs of all tiles in a given tileset
    to the first hitbox created with the Tiled Tile Collision Editor.
    If no hitbox is found, it uses the dimensions of the Tile's image.

    This function currently only works with rectangular hitboxes.

    :return: Dictionary mapping the IDs of all tiles in a given tileset to its
             hitbox (x, y, width, height)
    """
    tree = ElementTree.parse(path_to_tileset)
    root = tree.getroot()

    objects = {}
    try:
        for child in root:
            next_object = _get_obj_hitbox(child, path=path_to_tileset)
            if next_object:
                objects[next_object.id] = next_object

    except KeyError as e:
        raise Exception(f"Malformed tileset {path_to_tileset}\n") from e
    return objects
