from dataclasses import dataclass, field

from src.enums import SeedType
from src.settings import Coordinate


@dataclass
class PlantInfo:
    plant_type: SeedType
    age: int = field(default=0)

    def __post_init__(self):
        if self.age < 0:
            raise ValueError("corrupt save file: plants cannot have a negative age")


@dataclass
class TileInfo:
    watered: bool
    pos: Coordinate
    plant_info: PlantInfo | None = field(default=None)
