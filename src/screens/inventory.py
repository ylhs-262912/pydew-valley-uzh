import pygame  # noqa
from src.gui.abstract_menu import AbstractMenu
from src.enums import FarmingTool, InventoryResource, GameState
from src.gui.components import Button, ImageButton


class InventoryMenu(AbstractMenu):
    _IR_TO_OVERLAY_IMG = {
        InventoryResource.WOOD: "wood",
        InventoryResource.CORN: "corn",
        InventoryResource.TOMATO: "tomato",
        InventoryResource.CORN_SEED: "corn_seed",
        InventoryResource.TOMATO_SEED: "tomato_seed"
    }
    _FT_TO_OVERLAY_IMG = {
        FarmingTool.AXE: "axe",
        FarmingTool.HOE: "hoe",
        FarmingTool.WATERING_CAN: "water"
    }

    def __init__(self, inventory: dict, switch_screen, overlay_frames, obj_frames):
        super().__init__("Inventory", (800, 800))
        self._inventory = inventory
        self.switch_screen = switch_screen
        self.overlay_frames = overlay_frames
        self.obj_frames = obj_frames

    def button_setup(self):
        button_size = (80, 80)
        for ir, count in self._inventory.items():
            match ir:
                case InventoryResource.APPLE:
                    img = self.obj_frames["apple"]
                case InventoryResource.WOOD:
                    img = self.obj_frames["wood"]
                case _:
                    img = self._IR_TO_OVERLAY_IMG[ir]
