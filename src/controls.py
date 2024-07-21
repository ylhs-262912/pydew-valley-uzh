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
    """
    Instances of this dataclass refer to an individual Control / Keybind and its respective type, text, value and state

    Attributes:
        control_type: ControlType of this control
        text: Text to describe the control (e.g. in the Settings/Keybinds menu)
        value: Integer value of this control.
               Should be set to one of the key constants included in PyGame (see https://pyga.me/docs/ref/key.html).
               Is not necessarily required during class instantiation but should be set afterwards.

        just_pressed: Boolean value which indicates
                      whether the key associated with this control has just been pressed or not.
        pressed: Boolean value which indicates whether the key associated with this control is pressed or not.
    """

    control_type: ControlType
    text: str
    value: int | None = None

    # Attributes that reflect the current control state and are excluded from the savestate
    just_pressed: bool = field(default=False, metadata={"exclude": True})
    pressed: bool = field(default=False, metadata={"exclude": True})

    def _control_as_dict(self) -> dict[str, str | int]:
        """Returns a dictionary representation of this Control instance,
        excluding attributes describing the current control state"""
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
        """Loads a Control instance from a (partial) dictionary representation.
        Ignores entries that do not map to any field of the Control instance."""
        control_attribute_list = [i.name for i in fields(self)]

        for control_attr_name, control_attr_val in d.items():
            if control_attr_name in control_attribute_list:
                setattr(self, control_attr_name, control_attr_val)

        if isinstance(self.control_type, str):
            self.control_type = ControlType(self.control_type)


class Controls(Control, Enum):
    """
    Enum which groups all necessary Control instances.
    """

    UP = (ControlType.key, "Up")
    DOWN = (ControlType.key, "Down")
    LEFT = (ControlType.key, "Left")
    RIGHT = (ControlType.key, "Right")

    USE = (ControlType.key, "Use")
    NEXT_TOOL = (ControlType.key, "Cycle Tools")
    NEXT_SEED = (ControlType.key, "Cycle Seeds")
    PLANT = (ControlType.key, "Plant Current Seed")
    INTERACT = (ControlType.key, "Interact")
    EMOTE_WHEEL = (ControlType.key, "Toggle Emote Wheel")

    @classmethod
    def as_dict(cls) -> dict[str, dict[str, str | int]]:
        """Maps the name of each member to the value returned by member._control_as_dict()
        :return: A dictionary representation of all Controls members.
        """
        return {
            i.name: cls[i.name]._control_as_dict()
            for i in cls
        }

    @classmethod
    def from_dict(cls, d: dict[str, dict[str, str | int]]):
        """Loads the attributes of all supplied Control dictionary representations.
        Ignores entries that do not map to any member of Controls."""
        control_name_list = [i.name for i in cls]

        for control_key, control_value in d.items():
            if control_key in control_name_list:
                cls[control_key]._control_from_dict(control_value)

    @classmethod
    def load_default_keybind(cls, control: Self, keybinds: dict[str, int] = None):
        """Loads a singular Control.value of the given Controls member from the supplied keybinds dictionary.
        The name of the given Controls member should correspond to the dictionary key of the keybind.
        If there is no corresponding key in the keybinds dictionary, the Control.value will be set to None.
        When no keybinds are supplied, the keybinds defined in DEFAULT_CONTROLS will be used."""
        if keybinds is None:
            keybinds = DEFAULT_CONTROLS
        control.value = keybinds.get(control.get_name())

    @classmethod
    def load_default_keybinds(cls, keybinds: dict[str, int] = None):
        """
        Loads the Control.value of all Controls members from the supplied keybinds dictionary.
        For each member of Controls that does not have a corresponding dictionary entry
        with the same key as the member's name, the member's Control value will be set to None.
        """
        for control in cls:
            cls.load_default_keybind(control, keybinds=keybinds)

    def get_name(self):
        """:return: Name (_name_ attribute) of the Controls member"""
        return self._name_

    @classmethod
    def all_controls(cls) -> Generator[Control, None, None]:
        """:return: A generator which yields all Controls members."""
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
    Controls.EMOTE_WHEEL.get_name(): pygame.K_e,
}
