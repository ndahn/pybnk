from typing import Any
from dearpygui import dearpygui as dpg

from pybnk.gui import style
from pybnk.hash import calc_hash, lookup_table


def calc_hash_dialog(
    default_value: str = "",
    *,
    title: str = "Calc Hash",
    tag: str = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    def on_label_changed(sender: str, label: str, user_data: Any) -> None:
        h = calc_hash(label)
        dpg.set_value(f"{tag}_hash", h)

    def on_hash_changed(sender: str, hash: str, user_data: Any) -> None:
        label = lookup_table.get(int(hash), "<?>")
        dpg.set_value(f"{tag}_label", label)

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
            label="Label",
            callback=on_label_changed,
            tag=f"{tag}_label",
        )
        dpg.add_input_text(
            label="Hash",
            decimal=True,
            callback=on_hash_changed,
            tag=f"{tag}_hash",
        )

        dpg.add_separator()
        dpg.add_text("Calculates an FNV-1a 32bit hash", color=style.blue)

    on_label_changed(f"{tag}_label", default_value, None)
    return tag
