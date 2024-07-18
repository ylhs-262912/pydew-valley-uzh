from __future__ import annotations

from abc import ABC

from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.overlay.soil import SoilLayer
from src.sprites.character import Character


class NPCBase(Character, AIBehaviour, ABC):
    soil_layer: SoilLayer
