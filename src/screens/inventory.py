import pygame  # noqa
from src.gui.menu.abstract_menu import AbstractMenu
from src.enums import FarmingTool, InventoryResource, GameState
from src.gui.menu.components import ImageButton
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from itertools import chain
from operator import itemgetter
from typing import Callable


class _IMButton(ImageButton):
    def __init__(self, content: pygame.Surface, rect: pygame.Rect, name: str):
        super().__init__(content, rect)
        self._name = name

    @property
    def text(self):
        return self._name


_SPACING_BETWEEN_ROWS = 20
_TOP_MARGIN = 200
_LEFT_MARGIN = 40
_BUTTON_SIZE = (80, 80)
_SECTION_TITLES = (
    "Resources",
    "Tools",
    "Equipment"
)
_AVAILABLE_TOOLS = ("axe", "hoe", "water")
_get_resource_count = itemgetter(1)


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

    def __init__(
            self,
            player,
            frames: dict,
            switch_screen: Callable,
            assign_tool: Callable,
            assign_seed: Callable
    ):
        super().__init__("Inventory", (SCREEN_WIDTH, 800))
        self._inventory = player.inventory
        self._av_tools = _AVAILABLE_TOOLS
        self.switch_screen = switch_screen
        self.assign_tool = assign_tool
        self.assign_seed = assign_seed
        self.overlay_frames = frames["overlay"]
        self.obj_frames = frames["level"]["objects"]
        self.cosmetic_frames = frames["cosmetics"]
        # Splitting this into three lists, because
        # the inventory's content can get updated with new resources,
        # and if tools are progressively handed over to the player,
        # the same requirement might appear for tools and personal items
        self._inv_buttons = []
        self._ft_buttons = []
        self.button_setup()

    def _prepare_img_for_ir_button(self, ir: InventoryResource, count: int):
        match ir:
            case InventoryResource.APPLE:
                btn_name = "apple"
                img = self.obj_frames["apple"]
            case _:
                btn_name = self._IR_TO_OVERLAY_IMG[ir]
                img = self.overlay_frames[btn_name]
        calc_rect = img.get_frect(center=(32, 32))
        calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
        amount = self.font.render(str(count), False, "black")
        blit_list = (
            (img, calc_rect),
            (amount, amount.get_frect(bottomright=(64, 64)))
        )
        calc_img.fblits(blit_list)  # faster than doing two separate blits
        return calc_img, btn_name

    def _inventory_part_btn_setup(self, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to see
        # how many of each resource they gathered,
        # and possibly assign them as their current seed
        # (if the selected one is a seed).
        generic_rect = pygame.Rect((0, 0), button_size)
        available_width_for_btns = (self.size[0] * 2 // 3)
        btns_per_line = available_width_for_btns // button_size[0]
        x_spacing = (available_width_for_btns % button_size[0]) // max(1, btns_per_line - 1)
        for button_no, (ir, count) in enumerate(
                filter(
                    _get_resource_count,
                    self._inventory.items()
                )
        ):
            calc_img, btn_name = self._prepare_img_for_ir_button(ir, count)
            row, column = divmod(button_no, btns_per_line)
            btn_rect = generic_rect.copy()
            btn_rect.x = _LEFT_MARGIN + button_size[0] * column + x_spacing * column
            btn_rect.y = _TOP_MARGIN + (button_size[1] + _SPACING_BETWEEN_ROWS) * row
            yield _IMButton(calc_img, btn_rect, btn_name)

    def _ft_btn_setup(self, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to select their current tool.
        rect = pygame.Rect((0, 0), button_size)
        rect.centerx = (self.rect.width / 2)
        for index, tool in enumerate(self._av_tools):
            img = self.overlay_frames[tool]
            calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
            calc_img.blit(img, img.get_frect(center=(32, 32)))
            btn_rect = rect.copy()
            btn_rect.y = _TOP_MARGIN + (button_size[1] + _SPACING_BETWEEN_ROWS) * index
            yield _IMButton(calc_img, btn_rect, tool)

    def _special_btn_setup(self):
        # TODO: this part requires separate icons for the goggles, the hat and all special items.
        # Part of the menu for items such as the goggles, the hat, etc.
        pass

    def button_action(self, text):
        if text in self._av_tools:
            self.assign_tool(text)
        if "seed" in text:
            self.assign_seed(text)

    def button_setup(self):
        self._inv_buttons.extend(self._inventory_part_btn_setup(_BUTTON_SIZE))
        self.buttons.extend(self._inv_buttons)
        self._ft_buttons.extend(self._ft_btn_setup(_BUTTON_SIZE))
        self.buttons.extend(self._ft_buttons)

    def draw_title(self):
        super().draw_title()
        top = SCREEN_HEIGHT / 20 + 75
        for i, section_name in enumerate(_SECTION_TITLES):
            text_surf = self.font.render(section_name, False, "black")
            text_rect = text_surf.get_frect(top=top, centerx=(self.rect.width * (i + 1)) / 4)

            bg_rect = pygame.Rect(0, 0, text_rect.width + 40, 50)
            bg_rect.center = text_rect.center

            pygame.draw.rect(self.display_surface, "white", bg_rect, 0, 4)
            self.display_surface.blit(text_surf, text_rect)

    def refresh_buttons_content(self):
        """Replace the existing buttons for available tools and resource count,
        in case the values change."""
        for btn in chain(self._inv_buttons, self._ft_buttons):
            self.buttons.remove(btn)
        self._inv_buttons.clear()
        self._ft_buttons.clear()
        self._inv_buttons.extend(
            self._inventory_part_btn_setup(_BUTTON_SIZE)
        )
        self._ft_buttons.extend(self._ft_btn_setup(_BUTTON_SIZE))
        self.buttons.extend(
            chain(
                self._inv_buttons,
                self._ft_buttons
            )
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                self.switch_screen(GameState.LEVEL)
