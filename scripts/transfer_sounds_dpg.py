from typing import Any, Type, Callable
from dataclasses import asdict
import dearpygui.dearpygui as dpg

from pybnk import Soundbank, calc_hash
from pybnk.transfer import copy_structure

from pybnk.gui.file_dialog import open_file_dialog
from pybnk.gui.localization import Localization, English, Chinese


def dpg_init():
    with dpg.font_registry():
        with dpg.font("NotoSansMonoCJKsc-Regular.otf", 18) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)

        dpg.bind_font(default_font)


def select_source_bank(sender: str, app_data: Any, user_data: Any) -> None:
    lang = get_language()
    path = open_file_dialog(
        title=lang["openfile_source_bank"],
        filetypes=[(lang["soundbank"], "json")],
    )
    if path:
        dpg.set_value("source_bank_path", path)


def select_dest_bank(sender: str, app_data: Any, user_data: Any) -> None:
    lang = get_language()
    path = open_file_dialog(
        title=lang["openfile_dest_bank"],
        filetypes=[(lang["soundbank"], "json")],
    )
    if path:
        dpg.set_value("dest_bank_path", path)


def open_id_lookup_dialog(callback: Callable[[list[str]], None]) -> None:
    lang = get_language()
    selected = set()

    def on_item_select(sender: str, state: bool, evt: str) -> None:
        if state:
            selected.add(evt)
        else:
            selected.discard(evt)

    def load_play_events():
        try:
            bnk_path = dpg.get_value("source_bank_path")
            bnk = Soundbank.load(bnk_path)
            play_events = bnk.find_events("Play")
            play_event_names = []

            for evt in play_events:
                name = evt.lookup_name()
                if name:
                    if name.startswith("Play_"):
                        name = name[5:]
                        play_event_names.append(name)
                # TODO should we include raw hashes?
                # If so, make sure they are handled properly
                # else:
                #    name = f"#{evt.id}"

            play_event_names.sort()
            
            dpg.delete_item("id_listbox", children_only=True)
            for evt in play_event_names:
                dpg.add_selectable(label=evt, parent="id_listbox", user_data=evt, callback=on_item_select)
        except Exception as e:
            raise e

    def apply():
        callback(list(sorted(selected)))
        dpg.delete_item(window)

    with dpg.window(
        tag="select_ids_window",
        autosize=True,
        no_saved_settings=True,
        on_close=dpg.delete_item,
    ) as window:
        dpg.add_text(tag="available_ids_label")
        dpg.add_child_window(tag="id_listbox", width=70, height=300, border=False)

        dpg.add_spacer(height=5)
        dpg.add_text(tag="select_ids_tooltip", color=(0, 55, 255, 255))
        dpg.add_button(
            tag="add_selected_button",
            callback=apply,
        )

    change_language(window, lang)
    load_play_events()


def open_calc_hash_dialog() -> None:
    lang = get_language()

    def update_hash(sender: str, text: str, user_data: Any):
        dpg.set_value("calc_hash_output", calc_hash(text))

    with dpg.window(
        tag="calc_hash_window",
        autosize=True,
        no_saved_settings=True,
        on_close=dpg.delete_item,
    ) as window:
        dpg.add_input_text(tag="calc_hash_input", callback=update_hash)
        dpg.add_input_text(tag="calc_hash_output", enabled=False, readonly=True)

    change_language(window, lang)


def execute_transfer() -> None:
    lang = get_language()

    src_bnk = Soundbank.load(dpg.get_value("source_bank_path"))
    dst_bnk = Soundbank.load(dpg.get_value("dest_bank_path"))

    # Get text from both boxes and split by lines
    src_wwise_lines = dpg.get_value("source_wwise_ids").strip().split("\n")
    dst_wwise_lines = dpg.get_value("dest_wwise_ids").strip().split("\n")

    # Filter out possible empty lines
    src_wwise_lines = [line for line in src_wwise_lines if line.strip()]
    dst_wwise_lines = [line for line in dst_wwise_lines if line.strip()]

    if not src_wwise_lines:
        raise ValueError(lang["error_no_lines"])

    if len(src_wwise_lines) != len(dst_wwise_lines):
        raise ValueError(lang["error_line_mismatch"])

    wwise_map = {
        src.strip(): dst.strip() for src, dst in zip(src_wwise_lines, dst_wwise_lines)
    }

    copy_structure(src_bnk, dst_bnk, wwise_map, quiet=False)


def get_language() -> Localization:
    return dpg.get_item_user_data("menu_language")


def change_language(root: str, lang: Localization) -> None:
    values = asdict(lang)
    todo = [root]

    while todo:
        widget = todo.pop()
        alias = dpg.get_item_alias(widget)
        label = values.get(alias)
        if label:
            if dpg.get_item_type(widget) == "mvAppItemType::mvText":
                dpg.set_value(widget, label)
            else:
                dpg.set_item_label(widget, label)

        todo.extend(dpg.get_item_children(widget, 1))


def setup_content() -> str:
    def select_language(sender: str, state: bool, lang: Type[Localization]) -> None:
        if not state:
            dpg.set_value(sender, True)
            return

        for child in dpg.get_item_children("menu_language", 1):
            dpg.set_value(child, False)

        dpg.set_value(sender, True)
        lang_instance = lang()
        dpg.set_item_user_data("menu_language", user_data=lang_instance)

        # Update all UI elements with new language
        change_language("main_window", lang_instance)

    def on_ids_selected(ids: list[str]) -> None:
        print(ids)
        # TODO
        pass

    lang = English()

    with dpg.window(tag="main_window", autosize=True) as main_window:
        with dpg.menu_bar():
            with dpg.menu(tag="menu_language", user_data=lang):
                dpg.add_menu_item(
                    label="English",
                    check=True,
                    default_value=True,
                    callback=select_language,
                    user_data=English,
                )
                dpg.add_menu_item(
                    label="中文",
                    check=True,
                    callback=select_language,
                    user_data=Chinese,
                )

        # Soundbank paths
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="source_bank_path",
                hint=lang["no_file_selected"],
            )
            dpg.add_button(
                arrow=True,
                direction=dpg.mvDir_Right,
                callback=select_source_bank,
            )
            dpg.add_text(tag="source_bank_label")

        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="dest_bank_path",
                hint=lang["no_file_selected"],
            )
            dpg.add_button(
                arrow=True,
                direction=dpg.mvDir_Right,
                callback=select_dest_bank,
            )
            dpg.add_text(tag="dest_bank_label")

        dpg.add_spacer(height=10)

        # Wwise IDs
        with dpg.group(horizontal=True):
            with dpg.child_window(border=False, auto_resize_x=True, auto_resize_y=True):
                dpg.add_text(tag="source_ids_label")
                dpg.add_input_text(
                    multiline=True,
                    tag="source_wwise_ids",
                    width=250,
                    height=250,
                )

            with dpg.child_window(border=False, auto_resize_x=True, auto_resize_y=True):
                dpg.add_text(tag="dest_ids_label")
                dpg.add_input_text(
                    multiline=True,
                    tag="dest_wwise_ids",
                    width=250,
                    height=250,
                )

        dpg.add_spacer(height=10)

        # Tools
        with dpg.group(horizontal=True):
            dpg.add_button(
                tag="open_id_dialog_button",
                callback=lambda s, a, u: open_id_lookup_dialog(on_ids_selected),
            )
            dpg.add_button(
                tag="open_hash_dialog_button",
                callback=open_calc_hash_dialog,
            )

        dpg.add_spacer(height=10)

        # Do the deed
        dpg.add_separator()

        dpg.add_button(
            tag="transfer_button",
            callback=execute_transfer,
        )

    change_language(main_window, lang)
    return main_window


def main():
    dpg.create_context()
    dpg_init()

    dpg.create_viewport(title="ERSoundbankHelper", width=550, height=600)
    main_window = setup_content()
    dpg.set_primary_window(main_window, True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
