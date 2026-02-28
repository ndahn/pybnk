from typing import Any, Callable
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, calc_hash
from pybnk.convenience import create_simple_sound
from pybnk.types import WwiseNode
from pybnk.gui import style
from pybnk.gui.helpers import create_widget


def create_simple_sound_dialog(
    bnk: Soundbank,
    callback: Callable[[list[WwiseNode]], None],
    *,
    default_name: str = "s123456789",
    title: str = "Create Simple Sound",
    tag: str = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    def update_name_and_id(sender: str, new_name: str, user_data: Any) -> None:
        if not new_name:
            return

        h = calc_hash(new_name)
        dpg.set_value(f"{tag}_hash", str(h))

    def on_okay() -> None:
        name = dpg.get_value(f"{tag}_name")
        nodes = create_simple_sound(
            bnk,
            name,
            wems,
            amx,
            volume=volume,
            avoid_repeats=avoid_repeats,
        )
        # TODO callback

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

        # TODO wems table
        # TODO actor mixer selector
        # TODO properties table
        # TODO avoid repeats
