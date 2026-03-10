from typing import Any, Callable
from pathlib import Path
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, calc_hash
from pybnk.convenience import create_simple_sound
from pybnk.node_types import Event, ActorMixer
from pybnk.enums import property_defaults
from pybnk.util import logger
from pybnk.gui import style
from pybnk.gui.widgets import add_properties_table, add_filepaths_table, add_node_widget


def create_simple_sound_dialog(
    bnk: Soundbank,
    callback: Callable[[Event, Event], None],
    *,
    default_name: str = "s100200300",
    title: str = "Create Simple Sound",
    tag: str = None,
) -> str:
    if not tag:
        tag = dpg.generate_uuid()
    elif dpg.does_item_exist(tag):
        dpg.delete_item(tag)

    properties: dict[str, float] = {
        "Volume": property_defaults["Volume"],
    }
    wem_paths: list[Path] = []

    def update_name_and_id(sender: str, new_name: str, user_data: Any) -> None:
        if not new_name:
            return

        h = calc_hash(new_name)
        dpg.set_value(f"{tag}_hash", str(h))

    def on_amx_selected(sender: str, amx: ActorMixer, user_data: Any) -> None:
        if amx:
            dpg.set_value(f"{tag}_actor_mixer", amx.id)

    def on_properties_changed(
        sender: str, new_properties: dict[str, float], user_data: Any
    ) -> None:
        properties.clear()
        properties.update(new_properties)

    def on_wems_changed(sender: str, paths: list[Path], user_data: Any) -> None:
        wem_paths.clear()
        wem_paths.extend(paths)

    def show_message(msg: str, color: tuple[int, int, int, int] = style.red) -> None:
        if not msg:
            dpg.hide_item(f"{tag}_notification")
            return

        dpg.configure_item(
            f"{tag}_notification",
            default_value=msg,
            color=color,
            show=True,
        )

    def on_okay() -> None:
        name = dpg.get_value(f"{tag}_name")
        if not name:
            show_message("Name not specified")
            return

        amx = int(dpg.get_value(f"{tag}_actor_mixer"))
        if amx <= 0:
            show_message("ActorMixer not specified")
            return

        if not wem_paths:
            show_message("No sounds specified")
            return

        show_message()
        avoid_repeats = dpg.get_value(f"{tag}_avoid_repeats")

        (play_evt, stop_evt), _, _ = create_simple_sound(
            bnk,
            name,
            wem_paths,
            amx,
            avoid_repeats=avoid_repeats,
            properties=properties,
        )

        logger.info(f"Created new sound {name} with {len(wem_paths)} sounds")

        callback(play_evt, stop_evt)
        show_message("Yay!", color=style.blue)

    with dpg.window(
        label=title,
        width=400,
        height=400,
        autosize=True,
        no_saved_settings=True,
        tag=tag,
        on_close=lambda: dpg.delete_item(window),
    ) as window:
        dpg.add_input_text(
            label="Name",
            default_value=default_name,
            callback=update_name_and_id,
            tag=f"{tag}_name",
        )
        dpg.add_input_text(
            label="Hash",
            default_value=str(calc_hash(default_name)),
            readonly=True,
            enabled=False,
            tag=f"{tag}_hash",
        )

        # Actor mixer selector
        add_node_widget(
            bnk.query,
            "ActorMixer",
            on_amx_selected,
            node_type=ActorMixer,
        )

        # Avoid repeats
        dpg.add_checkbox(
            label="Avoid Repeats",
            default_value=False,
            tag=f"{tag}_avoid_repeats",
        )

        # Properties
        dpg.add_spacer(height=5)
        add_properties_table(properties, on_properties_changed)

        # WEMs
        dpg.add_spacer(height=5)
        add_filepaths_table(
            wem_paths,
            on_wems_changed,
            title="WEMs",
            filetypes={"Wwise Audio (.wem)": "*.wem"},
        )

        dpg.add_separator()
        dpg.add_text(show=False, tag=f"{tag}_notification", color=style.red)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Okay", callback=on_okay, tag=f"{tag}_button_okay")
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item(window),
            )

    return tag
