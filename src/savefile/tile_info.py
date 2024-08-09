from dataclasses import dataclass, field
from src.enums import SeedType
from src.settings import Coordinate


@dataclass
class PlantInfo:
    plant_type: SeedType
    age: int = field(default=0)


@dataclass
class TileInfo:
    pos: Coordinate
    plant_info: PlantInfo | None = field(default=None)

