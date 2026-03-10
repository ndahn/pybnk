from typing import Any
import colorsys
from dearpygui import dearpygui as dpg


# https://coolors.co/palette/ffbe0b-fb5607-ff006e-8338ec-3a86ff
yellow = (255, 190, 11, 255)
orange = (251, 86, 7, 255)
red = (234, 11, 30, 255)
pink = (255, 0, 110, 255)
purple = (127, 50, 236, 255)
blue = (58, 134, 255, 255)
green = (138, 201, 38, 255)

white = (255, 255, 255, 255)
light_grey = (151, 151, 151, 255)
dark_grey = (62, 62, 62, 255)
black = (0, 0, 0, 255)

light_blue = (112, 214, 255, 255)
light_green = (112, 255, 162, 255)
light_red = (255, 112, 119)


class themes:
    notification_frame = None
    item_default = None
    item_blue = None
    link_button = None
    no_padding = None


def init_themes():
    # Global theme
    bg_elements = [
        (
            dpg.mvThemeCol_WindowBg,
            dpg.mvThemeCol_ChildBg,
            dpg.mvThemeCol_PopupBg,
            dpg.mvThemeCol_TitleBg,
            dpg.mvThemeCol_TitleBgCollapsed,
            dpg.mvThemeCol_ResizeGrip,
        ),
        (
            dpg.mvThemeCol_FrameBg,
            dpg.mvThemeCol_MenuBarBg,
            dpg.mvThemeCol_ScrollbarBg,
            dpg.mvThemeCol_Button,
            dpg.mvThemeCol_Header,
            dpg.mvThemeCol_ResizeGripHovered,
            dpg.mvThemeCol_ResizeGripActive,
            dpg.mvThemeCol_Tab,
        ),
        (
            dpg.mvThemeCol_Border,
            dpg.mvThemeCol_BorderShadow,
            dpg.mvThemeCol_Separator,
            dpg.mvThemeCol_SeparatorHovered,
            dpg.mvThemeCol_SeparatorActive,
        ),
    ]

    # https://coolors.co/18181d-202229-32333c-1b97ea
    shades = [(24, 24, 29), (32, 34, 41), (50, 51, 60)]

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_FrameRounding, 2, category=dpg.mvThemeCat_Core
            )

            for shade, elements in zip(shades, bg_elements):
                for elem in elements:
                    dpg.add_theme_color(elem, shade, category=dpg.mvThemeCat_Core)

        # Disabled components
        with dpg.theme_component(dpg.mvInputFloat, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, [168, 168, 168])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [96, 96, 96])

        with dpg.theme_component(dpg.mvInputInt, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, [168, 168, 168])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [96, 96, 96])

        with dpg.theme_component(dpg.mvInputText, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, [168, 168, 168])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [96, 96, 96])

        with dpg.theme_component(dpg.mvCheckbox, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, [168, 168, 168])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [96, 96, 96])

    dpg.bind_theme(global_theme)

    # Additional themes
    with dpg.theme() as themes.notification_frame:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding, 7, 0, category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_FramePadding, 4, 4, category=dpg.mvThemeCat_Core
            )

    with dpg.theme() as themes.item_default:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_Border, (0, 0, 0), category=dpg.mvThemeCat_Core
            )

    with dpg.theme() as themes.item_blue:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text, (27, 151, 234), category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_Border, (27, 151, 234), category=dpg.mvThemeCat_Core
            )

    with dpg.theme() as themes.link_button:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text, light_blue, category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_Button, (0, 0, 0, 0), category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                (255, 255, 255, 40),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonActive,
                (255, 255, 255, 80),
                category=dpg.mvThemeCat_Core,
            )

    with dpg.theme() as themes.no_padding:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core
            )


class HighContrastColorGenerator:
    """Generates RGB colors with a certain distance apart so that subsequent colors are visually distinct."""

    def __init__(
        self,
        initial_hue: float = 0.0,
        hue_step: float = 0.61803398875,
        saturation: float = 1.0,
        value: float = 1.0,
    ):
        # 0.61803398875: golden ratio conjugate, ensures well-spaced hues
        self.hue_step = hue_step
        self.hue = initial_hue
        self.saturation = saturation
        self.value = value
        self.initial_hue = initial_hue
        self.cache = {}

    def __iter__(self):
        """Allows the class to be used as an iterable."""
        return self

    def reset(self) -> None:
        self.hue = self.initial_hue
        self.cache.clear()

    def __next__(self) -> tuple[int, int, int]:
        """Generates the next high-contrast color."""
        self.hue = (self.hue + self.hue_step) % 1
        r, g, b = colorsys.hsv_to_rgb(self.hue, self.saturation, self.value)
        return (int(r * 255), int(g * 255), int(b * 255))

    def __call__(self, key: Any = None) -> tuple[int, int, int]:
        """Allows calling the instance directly to get the next color."""
        if key is not None:
            if key not in self.cache:
                self.cache[key] = next(self)
            return self.cache[key]

        return next(self)
