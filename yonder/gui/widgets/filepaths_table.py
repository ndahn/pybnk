from typing import Any, Callable, TypeVar
from pathlib import Path
from dearpygui import dearpygui as dpg

from yonder.gui.helpers import shorten_path
from yonder.gui.dialogs.file_dialog import open_multiple_dialog, choose_folder


_T = TypeVar("_T")


def add_widget_table(
    initial_values: list[_T],
    new_item: Callable[[], _T],
    add_row_widgets: Callable[[_T], tuple[str, ...]],
    on_value_changed: Callable[[str, list[_T], Any], None],
    *,
    add_item_label: str = "+",
    label: str = None,
    tag: str | int = 0,
    user_data: Any = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    current_values: list[_T] = list(initial_values)
    row_widgets: list[tuple[int, int]] = []

    def refresh() -> None:
        dpg.delete_item(tag, children_only=True, slot=1)
        for val in current_values:
            add_row(val)
        add_footer()

    def on_remove_clicked(sender: int) -> None:
        idx = next(i for i, ids in enumerate(row_widgets) if sender in ids)
        current_values.pop(idx)
        row_widgets.pop(idx)
        refresh()
        on_value_changed(tag, list(current_values), user_data)

    def on_add_clicked() -> None:
        result = new_item()
        if not result:
            return

        if not isinstance(result, list):
            result = [result]

        current_values.extend(result)
        refresh()
        on_value_changed(tag, list(current_values), user_data)

    def add_row(val: _T) -> None:
        with dpg.table_row(parent=tag):
            widget_ids = add_row_widgets(val)
            remove_id = dpg.add_button(label="-", callback=on_remove_clicked)
            row_widgets.append(tuple(widget_ids) + (remove_id,))

    def add_footer() -> None:
        with dpg.table_row(parent=tag):
            dpg.add_button(label=add_item_label, callback=on_add_clicked)

    # The actual widgets
    if label:
        dpg.add_text(label)

    with dpg.table(
        header_row=False,
        policy=dpg.mvTable_SizingFixedFit,
        borders_outerH=True,
        borders_outerV=True,
        tag=tag,
    ):
        dpg.add_table_column(
            label="Value", width_stretch=True, init_width_or_weight=100
        )
        dpg.add_table_column(label="")

        refresh()

    return tag


def add_filepaths_table(
    initial_paths: list[Path],
    on_value_changed: Callable[[str, list[Path], Any], None],
    *,
    folders: bool = False,
    label: str = "Files",
    filetypes: dict[str, str] = None,
    tag: str | int = 0,
    user_data: Any = None,
) -> str:
    def add_item() -> Path:
        if folders:
            res = choose_folder(title=label)
        else:
            res = open_multiple_dialog(title=label, filetypes=filetypes)

        if res:
            return Path(res)

        return None

    def add_row_widgets(path: Path):
        txt = dpg.add_input_text(
            default_value=shorten_path(path, maxlen=40),
            enabled=False,
            readonly=True,
            width=-1,
        )
        return (txt, )

    return add_widget_table(
        initial_paths,
        add_item,
        on_value_changed,
        add_item_label="+ Add Paths" if folders else "+ Add Files",
        add_row_widgets=add_row_widgets,
        label=label,
        tag=tag,
        user_data=user_data,
    )


def add_floats_table(
    initial_values: list[tuple[str, float]],
    on_value_changed: Callable[[str, list[tuple[str, float]], Any], None],
    *,
    label: str = "Files",
    tag: str | int = 0,
    user_data: Any = None,
) -> str:
    def add_item() -> tuple[str, float]:
        return ("<new>", 0.0)

    def add_row_widgets(item: tuple[str, float]) -> tuple[str, ...]:
        label = dpg.add_input_text(default_value=item[0])
        value = dpg.add_input_float(default_value=item[1], width=-1)
        return (label, value)

    return add_widget_table(
        initial_values,
        add_item,
        on_value_changed,
        add_item_label="+ Add Value",
        add_row_widgets=add_row_widgets,
        label=label,
        tag=tag,
        user_data=user_data,
    )
