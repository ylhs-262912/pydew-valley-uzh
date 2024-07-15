from collections.abc import Generator
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Self

import pygame


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

    def _control_as_dict(self) -> dict[str, str | int]:
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

    def _control_from_dict(self, d: dict[str, str | int]):
        control_attribute_list = [i.name for i in fields(self)]

        for control_attr_name, control_attr_val in d.items():
            if control_attr_name in control_attribute_list:
                setattr(self, control_attr_name, control_attr_val)

        if isinstance(self.type, str):
            self.type = ControlType(self.type)


class Controls(Control, Enum):
    UP = (ControlType.key, "Up")
    DOWN = (ControlType.key, "Down")
    LEFT = (ControlType.key, "Left")
    RIGHT = (ControlType.key, "Right")

    USE = (ControlType.key, "Use")
    NEXT_TOOL = (ControlType.key, "Cycle Tools")
    NEXT_SEED = (ControlType.key, "Cycle Seeds")
    PLANT = (ControlType.key, "Plant Current Seed")
    INTERACT = (ControlType.key, "Interact")

    @classmethod
    def as_dict(cls) -> dict[str, dict[str, str | int]]:
        return {
            i.name: cls[i.name]._control_as_dict()
            for i in cls
        }

    @classmethod
    def from_dict(cls, d: dict[str, dict[str, str | int]]):
        control_name_list = [i.name for i in cls]

        for control_key, control_value in d.items():
            if control_key in control_name_list:

                cls[control_key]._control_from_dict(control_value)

    @classmethod
    def load_default_keybind(cls, control: Self, keybinds: dict[str, int] = None):
        if keybinds is None:
            keybinds = DEFAULT_CONTROLS
        control.value = keybinds.get(control.get_name())

    @classmethod
    def load_default_keybinds(cls, keybinds: dict[str, int] = None):
        for control in cls:
            cls.load_default_keybind(control, keybinds=keybinds)

    def get_name(self):
        return self._name_

    @classmethod
    def all_controls(cls) -> Generator[Control, None, None]:
        return (getattr(cls, i.name) for i in cls)


DEFAULT_CONTROLS = {
    Controls.UP.get_name(): pygame.K_UP,
    Controls.DOWN.get_name(): pygame.K_DOWN,
    Controls.LEFT.get_name(): pygame.K_LEFT,
    Controls.RIGHT.get_name(): pygame.K_RIGHT,

    Controls.USE.get_name(): pygame.K_SPACE,
    Controls.NEXT_TOOL.get_name(): pygame.K_TAB,
    Controls.NEXT_SEED.get_name(): pygame.K_LSHIFT,
    Controls.PLANT.get_name(): pygame.K_RETURN,
    Controls.INTERACT.get_name(): pygame.K_i,
}
