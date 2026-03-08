from typing import Any, Callable
from dearpygui import dearpygui as dpg

from pybnk import Node
from pybnk.node_types import MusicSwitchContainer
from pybnk.hash import lookup_name, calc_hash
from pybnk.gui import style
from pybnk.gui.widgets import add_generic_widget


def create_state_path_dialog(
    node: MusicSwitchContainer,
    callback: Callable[[str, list[str], int], None],
    *,
    title: str = "New State Path",
    tag: str = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    leaf_node_id: int = 0

    def on_node_selected(sender: str, leaf_node: int | Node, user_data: Any) -> None:
        nonlocal leaf_node_id
        if isinstance(leaf_node, Node):
            leaf_node = leaf_node.id
        leaf_node_id = leaf_node

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
        if leaf_node_id <= 0:
            show_message("Leaf node ID not set")
            return

        keys = []
        for arg in node.arguments:
            name = lookup_name(arg, f"#{arg}")
            key: str = dpg.get_value(f"{tag}_arg_{arg}")

            if not key:
                show_message(f"{name}: value must not be empty")
                return

            if key == "*":
                key_val = 0
            elif key.startswith("#"):
                try:
                    key_val = int(key[1:])
                except ValueError:
                    show_message(f"{name}: value is not a valid hash")
                    return
            else:
                key_val = calc_hash(key)

            keys.append(key_val)

        callback(tag, keys, leaf_node_id)
        dpg.delete_item(window)

    with dpg.window(
        label=title,
        width=400,
        height=400,
        autosize=True,
        no_saved_settings=True,
        tag=tag,
        on_close=lambda: dpg.delete_item(window),
    ) as window:
        # For these decision trees all branches have the same length,
        # which makes it so much easier for us!
        for arg in node.arguments:
            name = lookup_name(arg, f"#{arg}")
            dpg.add_input_text(label=name, default_value="*", tag=f"{tag}_arg_{arg}")

        dpg.add_spacer(height=3)
        add_generic_widget(Node, "Node", on_node_selected, default=0)

        dpg.add_separator()
        dpg.add_text(show=False, tag=f"{tag}_notification", color=style.red)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Okay", callback=on_okay, tag=f"{tag}_button_okay")
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item(window),
            )
