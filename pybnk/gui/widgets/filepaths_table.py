from typing import Any, Callable
from pathlib import Path
from dearpygui import dearpygui as dpg

from pybnk.gui.helpers import shorten_path
from pybnk.gui.dialogs.file_dialog import open_multiple_dialog, choose_folder


def add_filepaths_table(
    initial_paths: list[Path],
    on_value_changed: Callable[[str, list[Path], Any], None],
    *,
    folders: bool = False,
    title: str = "Files",
    filetypes: dict[str, str] = None,
    tag: str | int = 0,
    user_data: Any = None,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    current_paths: list[Path] = list(initial_paths)

    def refresh() -> None:
        dpg.delete_item(tag, children_only=True, slot=1)
        for path in current_paths:
            add_row(path)
        add_footer()

    def on_remove_clicked(sender: int) -> None:
        idx = next(i for i, ids in enumerate(row_widgets) if ids[1] == sender)
        current_paths.pop(idx)
        row_widgets.pop(idx)
        refresh()
        on_value_changed(tag, list(current_paths), user_data)

    def on_add_clicked() -> None:
        if folders:
            result = choose_folder(title=title)
        else:
            result = open_multiple_dialog(title=title, filetypes=filetypes)
        
        if not result:
            return

        if not isinstance(result, list):
            result = [result]

        current_paths.extend(Path(p) for p in result if p)
        refresh()
        on_value_changed(tag, list(current_paths), user_data)

    def add_row(path: Path) -> None:
        with dpg.table_row(parent=tag):
            text_id = dpg.add_input_text(
                default_value=shorten_path(path, maxlen=40),
                enabled=False,
                readonly=True,
                width=-1,
            )
            remove_id = dpg.add_button(label="-", callback=on_remove_clicked)
            row_widgets.append((text_id, remove_id))

    def add_footer() -> None:
        with dpg.table_row(parent=tag):
            dpg.add_button(label="+ Add Files", callback=on_add_clicked)

    row_widgets: list[tuple[int, int]] = []

    # The actual widgets
    dpg.add_text(title)

    with dpg.table(
        header_row=False,
        policy=dpg.mvTable_SizingFixedFit,
        borders_outerH=True,
        borders_outerV=True,
        tag=tag,
    ):
        dpg.add_table_column(label="File", width_stretch=True, init_width_or_weight=100)
        dpg.add_table_column(label="")
        
        refresh()

    return tag
