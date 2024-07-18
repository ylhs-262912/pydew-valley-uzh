import pygame  # noqa
from src.gui.abstract_menu import AbstractMenu
from src.enums import FarmingTool, InventoryResource, GameState
from src.gui.components import ImageButton
from src.settings import SCREEN_WIDTH


class _IRButton(ImageButton):
    def __init__(self, content: pygame.Surface, rect: pygame.Rect, name: str):
        super().__init__(content, rect)
        self._name = name

    @property
    def text(self):
        return self._name


_SPACING_BETWEEN_ROWS = 20


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

    def __init__(self, inventory: dict, available_tools: list[str], switch_screen, overlay_frames, obj_frames):
        super().__init__("Inventory", (SCREEN_WIDTH, 800))
        self._inventory = inventory
        self._av_tools = available_tools
        self.switch_screen = switch_screen
        self.overlay_frames = overlay_frames
        self.obj_frames = obj_frames

    def _inventory_part_btn_setup(self, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to see
        # how many of each resource they gathered,
        # and possibly assign them as their current seed
        # (if the selected one is a seed).
        generic_rect = pygame.Rect((0, 0), button_size)
        available_width_for_btns = (self.size[0] // 2)
        btns_per_line = available_width_for_btns // button_size[0]
        x_spacing = (available_width_for_btns % button_size[0]) // max(1, btns_per_line[0] - 1)
        for button_no, (ir, count) in enumerate(self._inventory.items()):
            match ir:
                case InventoryResource.APPLE:
                    btn_name = "apple"
                    img = self.obj_frames["apple"]
                case InventoryResource.WOOD:
                    btn_name = "wood"
                    img = self.obj_frames["wood"]
                case _:
                    btn_name = self._IR_TO_OVERLAY_IMG[ir]
                    img = self.overlay_frames[btn_name]
            calc_rect = img.get_frect(center=(32, 32))
            calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
            amount = self.font.render(str(count), False, "grey")
            blit_list = (
                (img, calc_rect),
                (amount, amount.get_frect(bottomright=(64, 64)))
            )
            calc_img.fblits(blit_list)  # faster than doing two separate blits
            row, column = divmod(button_no, btns_per_line)
            btn_rect = generic_rect.copy()
            spaces = (column - 1)
            btn_rect.x = button_size[0]*spaces + x_spacing * spaces
            btn_rect.y = button_size[1]*(row - 1) + _SPACING_BETWEEN_ROWS * spaces
            yield _IRButton(calc_img, btn_rect, btn_name)

    def _ft_btn_setup(self, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to select their current tool.
        for index, tool in enumerate(self._av_tools):
            img = self.overlay_frames[tool]
            calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
            calc_img.blit(img, img.get_frect(center=(32, 32)))

    def _special_btn_setup(self):
        # Part of the menu for items such as the goggles, the hat, etc.
        pass

    def button_setup(self):
        button_size = (80, 80)
        self.buttons.extend(self._inventory_part_btn_setup(button_size))

