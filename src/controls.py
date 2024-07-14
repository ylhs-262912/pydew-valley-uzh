from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Self

import pygame


# TODO: Enable the default control dictionary to use Fields of the Controls dataclass as keys, instead of raw strings
DEFAULT_CONTROLS = {
    "UP": pygame.K_UP,
    "DOWN": pygame.K_DOWN,
    "LEFT": pygame.K_LEFT,
    "RIGHT": pygame.K_RIGHT,

    "USE": pygame.K_SPACE,
    "NEXT_TOOL": pygame.K_TAB,
    "NEXT_SEED": pygame.K_LSHIFT,
    "PLANT": pygame.K_RETURN,
    "INTERACT": pygame.K_i,
}


class ControlType(Enum):
    key = "key"
    mouse = "mouse"


@dataclass
class Control:
    type: ControlType
    text: str
    value: int | None = None

    just_pressed: bool = field(default=False, metadata={"exclude": True})
    pressed: bool = field(default=False, metadata={"exclude": True})

    def as_dict(self) -> dict[str, str | int]:
        return_dict = {}
        for _field in fields(self):
            if _field.metadata.get("exclude"):
                continue

            name = _field.name
            value = getattr(self, name)
            if isinstance(value, ControlType):
                return_dict[name] = value.value
            else:
                return_dict[name] = value

        return return_dict

    @classmethod
    def from_dict(cls, d: dict[str, str | int]) -> Self:
        obj = cls(**d)
        obj.type = ControlType(obj.type)
        return obj


@dataclass
class Controls:
    UP: Control = (ControlType.key, "Up")
    DOWN: Control = (ControlType.key, "Down")
    LEFT: Control = (ControlType.key, "Left")
    RIGHT: Control = (ControlType.key, "Right")

    USE: Control = (ControlType.key, "Use")
    NEXT_TOOL: Control = (ControlType.key, "Cycle Tools")
    NEXT_SEED: Control = (ControlType.key, "Cycle Seeds")
    PLANT: Control = (ControlType.key, "Plant Current Seed")
    INTERACT: Control = (ControlType.key, "Interact")

    def __post_init__(self):
        for _field in fields(self):
            name = _field.name
            value = getattr(self, name)
            setattr(self, name, Control(type=value[0], text=value[1]))

    def as_dict(self) -> dict[str, dict[str, str | int]]:
        return {
            i.name: getattr(self, i.name).as_dict() for i in fields(self)
        }

    def from_dict(self, d: dict[str, dict[str, str | int]]):
        for key, value in d.items():
            setattr(self, key, Control.from_dict(value))

    def load_default_keybind(self, control: str, keybinds: dict[int, int] = None):
        if keybinds is None:
            keybinds = DEFAULT_CONTROLS
        getattr(self, control).value = keybinds.get(control)

    def load_default_keybinds(self, keybinds: dict[int, int] = None):
        for control in self.__dict__.keys():
            self.load_default_keybind(control, keybinds=keybinds)
