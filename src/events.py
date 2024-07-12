"""Expansion over Pygame's event management system."""
import pygame
from typing import Union, Type, NoReturn
from types import UnionType, NoneType

SpecialForm = type(NoReturn)


class _EventDefinition:
    """Additional information about a specific event type.

    This allows us to ensure that all required arguments are given
    when posting an event of a certain type (namely, by raising errors if they
    aren't given)."""

    _EDEF_CACHE = {}  # INTERNAL USAGE!
    __slots__ = ("name", "__name__", "code", "attrs", "default_values_for_attrs")

    @classmethod
    def from_code(cls, code: int) -> "_EventDefinition":
        """Return the corresponding event definition for a given code."""
        try:
            return cls._EDEF_CACHE[code]
        except LookupError:
            raise ValueError(f"given code ({code}) is not linked to a registered event type")

    @classmethod
    def add_to_edef_cache(cls, edef: "_EventDefinition"):
        """Add the given event definition to the cache."""
        cls._EDEF_CACHE[edef.code] = edef

    def __init__(
        self,
        name: str,
        code: int,
        **attrs: Union[Type, SpecialForm],
    ):
        self.__name__ = self.name = name
        self.attrs = attrs
        self.default_values_for_attrs = {}
        self.code = code

    def __repr__(self):
        return f"<EventDefinition(name='{self.__name__}', code={self.code}, {', '.join((f'{attr}:{value}' for attr, value in self.attrs.items()))}>"

    def __hash__(self):
        return hash(
            (self.__name__, self.code) + tuple(itm for itm in self.attrs.items())
        )

    def set_default_for_attr(self, attr: str, value):
        if attr not in self.attrs:
            raise ValueError(
                f"invalid attribute for event type {self.__name__} : '{attr}'"
            )
        else:
            self.default_values_for_attrs[attr] = value

    def __call__(self, **attrs):
        if self.attrs:
            for attr in attrs:
                try:
                    assert attr in self.attrs
                except AssertionError as err:
                    raise TypeError(
                        f"unexpected attributes for event type '{self.__name__}'"
                    ) from err
            for attr, attr_type in self.attrs.items():
                if attr in attrs:
                    continue
                else:
                    if "Optional" in repr(attr_type):
                        pass
                    elif isinstance(attr_type, UnionType) and NoneType in attr_type.__args__:
                        pass
                    elif attr in self.default_values_for_attrs:
                        attrs[attr] = self.default_values_for_attrs[attr]
                    else:
                        raise TypeError(
                            f"missing argument for event type '{self.__name__}' : '{attr}'"
                        )
        else:
            if attrs:
                raise TypeError(
                    f"event type '{self.__name__}' does not take any attributes"
                )
        return pygame.event.Event(self.code, **attrs)


def get_event_def(code: int) -> _EventDefinition:
    """Return the corresponding event type specification for the given code.

    :param code: The code you wish to retrive the event specs of.
    :return: The corresponding definition."""
    return _EventDefinition.from_code(code)


def create_custom_event_type(name: str, **attributes: Union[Type, SpecialForm]) -> int:
    """Register a new event type and its specifications.

    :param name: The definition name (will be used in mostly error messages).
    :param attributes: The event's required attributes. If empty,
    trying to add any attributes to an event of this type will result in
    a TypeError being raised."""
    created_code = pygame.event.custom_type()
    edef = _EventDefinition(name, created_code, **attributes)
    _EventDefinition.add_to_edef_cache(edef)
    return created_code

