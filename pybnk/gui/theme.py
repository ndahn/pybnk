from dearpygui import dearpygui as dpg


class themes:
    item_default = None
    item_blue = None


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
    shades = [
        (24, 24, 29),
        (32, 34, 41),
        (50, 51, 60)
    ]

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2, category=dpg.mvThemeCat_Core)

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
    with dpg.theme() as themes.item_default:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0), category=dpg.mvThemeCat_Core)

    with dpg.theme() as themes.item_blue:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (27, 151, 234), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (27, 151, 234), category=dpg.mvThemeCat_Core)
