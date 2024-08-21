from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.ai_behaviour_tree_base import (
    Action,
    Context,
    NodeWrapper,
    Selector,
)
from src.npc.utils import pf_wander


@dataclass
class ChickenIndividualContext(Context):
    chicken: ChickenBase


def wander(context: ChickenIndividualContext) -> bool:
    return pf_wander(context.chicken)


class ChickenBehaviourTree(NodeWrapper, Enum):
    Wander = Selector(Action(wander))
