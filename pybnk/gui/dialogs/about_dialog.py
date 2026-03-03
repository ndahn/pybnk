import os
import sys
from dearpygui import dearpygui as dpg
import webbrowser

from pybnk.gui import style


def about_dialog(*, tag: str = None, **window_args) -> str:
    if not tag:
        tag = f"about_dialog_{dpg.generate_uuid()}"

    color = (48, 48, 48, 255)

    if not dpg.does_item_exist("pybnk_splash"):
        with dpg.texture_registry():
            root = os.path.dirname(sys.argv[0])
            # TODO create proper main, remove relative offset
            splash_img = os.path.abspath(os.path.join(root, "../..", "docs/images/misty_cliffs.jpg"))
            w, h, ch, data = dpg.load_image(splash_img)
            dpg.add_static_texture(w, h, data, tag="pybnk_splash")

    with dpg.window(
        width=410,
        height=230,
        label="About",
        no_saved_settings=True,
        on_close=lambda: dpg.delete_item(dialog),
        no_scrollbar=True,
        no_scroll_with_mouse=True,
        no_resize=True,
        tag=tag,
        **window_args,
    ) as dialog:
        from pybnk import __version__

        with dpg.group(horizontal=True):
            dpg.add_image("pybnk_splash", width=410, height=230)
            
            with dpg.group(pos=(10, 30)):
                dpg.add_text(f"Banks of Yonder v{__version__}", color=color)

                dpg.add_text("Written by Nikolas Dahn", color=color)
                dpg.add_button(
                    label="https://github.com/ndahn/pybnk",
                    small=True,
                    callback=lambda: webbrowser.open(
                        "https://github.com/ndahn/pybnk"
                    ),
                )
                dpg.bind_item_theme(dpg.last_item(), style.themes.link_button)

                dpg.add_text("Bugs, questions, feature request?", color=color)
                dpg.add_text("Find me on ?ServerName? @Managarm!", color=color)

    dpg.bind_item_theme(dialog, style.themes.no_padding)

    return tag
