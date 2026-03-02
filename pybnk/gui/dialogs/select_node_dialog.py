from typing import Any, Callable, Iterable, Type, TypeVar
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node


_T = TypeVar("_T", bound=Type[Node])


def select_node_dialog(
    get_items: Callable[[str], Iterable[Node]],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    max_items: int = 200,
    title: str = "Select Node",
    tag: str = 0,
    user_data: Any = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    items: dict[str, Node] = {}
    selected_item: Node = None

    def on_filter_changed(sender: str, filt: str, user_data: Any) -> None:
        items.clear()
        items.update(
            {
                f"{x.lookup_name('<?>')} ({x.id})": x
                for i, x in enumerate(get_items(filt))
                if i < max_items
            }
        )
        dpg.configure_item(f"{tag}_items", items=list(items.keys()))

    def on_item_selected(sender: str, item: str, user_data: Any) -> None:
        nonlocal selected_item
        selected_item = items[item]

    def on_okay() -> None:
        if not selected_item:
            return

        on_node_selected(tag, selected_item, user_data)
        dpg.delete_item(window)

    with dpg.window(
        label=title,
        width=250,
        height=400,
        autosize=True,
        no_saved_settings=True,
        tag=tag,
        on_close=lambda: dpg.delete_item(window),
    ) as window:
        dpg.add_input_text(
            callback=on_filter_changed,
            hint="Filter...",
            tag=f"{tag}_filter",
        )
        dpg.add_listbox(
            callback=on_item_selected,
            num_items=15,
            tag=f"{tag}_items",
        )

        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_button(label="Okay", callback=on_okay, tag=f"{tag}_button_okay")
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item(window),
            )

    on_filter_changed(f"{tag}_filter", "", None)
    return tag


def select_node_of_type(
    bnk: Soundbank,
    node_type: _T,
    on_node_selected: Callable[[str, _T, Any], None],
    *,
    tag: str = 0,
    user_data: Any = None,
) -> str:
    candidates = list(bnk.query({"type": node_type.__name__}))

    def get_nodes(filt: str) -> list[_T]:
        if not filt:
            return candidates

        return [n for n in candidates if filt in f"{n.lookup_name('')}{n.id}"]

    return select_node_dialog(
        get_nodes,
        on_node_selected,
        tag=tag,
        user_data=user_data
    )
