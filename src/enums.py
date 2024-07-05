from enum import Enum, IntEnum


class PlayerState(IntEnum):
    IDLE = 0
    WALK = 1


class ItemToUse(IntEnum):
    """Both available options for Player.use_tool. If any more have to be added, put them as members of this enum."""
    REGULAR_TOOL = 0
    SEED = 1


_FT_SERIALISED_STRINGS = (
    "none",
    "axe",
    "hoe",
    "water",
    "corn seed",
    "tomato seed"
)


class FarmingTool(IntEnum):
    """Notably used to distinguish the different farming tools (including seeds) in-code."""
    NONE = 0  # Possible placeholder value if needed somewhere
    AXE = 1
    HOE = 2
    WATERING_CAN = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    @property
    def _swinging_tools(self):
        return {self.HOE, self.AXE}

    def is_swinging_tool(self):
        return self in self._swinging_tools

    @classmethod
    def get_first_tool_id(cls):
        """Return the first tool ID. This might change in the course of development."""
        return cls.AXE

    @classmethod
    def get_tool_count(cls):
        return cls.get_first_seed_id() - cls.get_first_tool_id()

    @classmethod
    def get_seed_count(cls):
        return len(cls) - cls.get_first_seed_id()

    @classmethod
    def get_first_seed_id(cls):
        """Same as get_first_tool_id, but for the seeds. Duh."""
        return cls.CORN_SEED

    def as_serialised_string(self):
        # We keep that method separate from the actual str dunder, so we can still get the original repr when debugging
        return _FT_SERIALISED_STRINGS[self]

    @classmethod
    def from_serialised_string(cls, val: str):
        """Return a FarmingTool enum member from a serialised string.

        :param val: The serialised string.
        :return: The corresponding enum member.
        :raise LookupError: if no enum member matches this string."""
        try:
            return cls(_FT_SERIALISED_STRINGS.index(val))
        except IndexError as exc:
            raise LookupError(f"serialised string '{val}' does not match any member in enum 'FarmingTool'") from exc


_IR_SERIALISED_STRINGS = (
    "wood",
    "apple",
    "corn",
    "tomato",
    "corn seed",
    "tomato seed"
)


class InventoryResource(IntEnum):
    """All stored items in the inventory."""
    WOOD = 0
    APPLE = 1
    CORN = 2
    TOMATO = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    def as_serialised_string(self):
        # We keep that method separate from the actual str dunder, so we can still get the original repr when debugging
        return _IR_SERIALISED_STRINGS[self]

    @classmethod
    def from_serialised_string(cls, val: str):
        """Return an InventoryResource enum member from a serialised string.

        :param val: The serialised string.
        :return: The corresponding enum member.
        :raise LookupError: if no enum member matches this string."""
        try:
            return cls(_IR_SERIALISED_STRINGS.index(val))
        except IndexError as exc:
            raise LookupError(f"serialised string '{val}' does not match any member in enum 'InventoryResource'") from exc

