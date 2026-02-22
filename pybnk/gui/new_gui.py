from typing import Any
from importlib import resources
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.types import Event, Action
from pybnk.util import logger
from pybnk.enums import ActionType
from pybnk.gui.file_dialog import open_file_dialog, save_file_dialog
from pybnk.gui.localization import Localization, English
from pybnk.gui.table_tree_nodes import (
    table_tree_node,
    table_tree_leaf,
    add_lazy_table_tree_node,
)


def dpg_init():
    with dpg.font_registry():
        import pybnk

        resource_file = resources.files(pybnk).joinpath(
            "resources/NotoSansMonoCJKsc-Regular.otf"
        )
        with resources.path(pybnk, resource_file) as path:
            with dpg.font(str(path), 18) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)

        dpg.bind_font(default_font)


class PyBnkGui:
    def __init__(self, tag: str = None):
        if tag is None:
            tag = dpg.generate_uuid()

        self.tag = tag
        self.language: Localization = English()
        self.bnk: Soundbank = None
        self.events: dict[int, Event] = {}
        self.max_events = 500

        self._setup_menu()
        self._setup_content()

    def _setup_menu(self) -> None:
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(
                    label="Open...",
                    shortcut="ctrl-o",
                    callback=self._open_soundbank,
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Save",
                    shortcut="ctrl-s",
                    callback=None,  # TODO
                )
                dpg.add_menu_item(
                    label="Save As...",
                    shortcut="ctrl-shift-s",
                    callback=None,  # TODO
                )

    def _setup_content(self) -> None:
        tag = self.tag

        with dpg.group(horizontal=True):
            with dpg.child_window(
                horizontal_scrollbar=False,
                width=200,
                resizable_x=True,
                autosize_y=True,
                tag=f"{tag}_events_window",
            ):
                dpg.add_input_text(hint="Filter...", width=-1, tag=f"{tag}_events_filter")
                dpg.add_text("Showing 0 events", tag=f"{tag}_events_count")
                with dpg.table(
                    no_host_extendX=True,
                    resizable=True,
                    borders_innerV=True,
                    policy=dpg.mvTable_SizingFixedFit,
                    header_row=False,
                    tag=f"{tag}_events_table",
                ):
                    dpg.add_table_column(label="Node", width_stretch=True)

            with dpg.child_window(
                autosize_x=True,
                autosize_y=True,
            ):
                dpg.add_child_window(
                    autosize_x=True,
                    auto_resize_y=True,
                    border=False,
                    tag=f"{tag}_attributes",
                )
                dpg.add_separator()
                with dpg.child_window(
                    autosize_x=True,
                    autosize_y=True,
                    border=False,
                ):
                    dpg.add_input_text(
                        multiline=True,
                        width=-1,
                        height=-30,
                        tag=f"{tag}_json",
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Apply",
                            callback=None, # TODO
                        )
                        dpg.add_button(
                            label="Reset",
                            callback=None, # TODO
                        )

    def _open_soundbank(self) -> None:
        lang = self.language
        path = open_file_dialog(
            title=lang.open,
            filetypes={lang.soundbank_files: "*.json"},
        )
        if path:
            self._load_soundbank(path)

    def _load_soundbank(self, path: str) -> None:
        logger.info(f"Loading soundbank {path}")
        bnk = Soundbank.load(path)

        self.clear()
        self.bnk = bnk
        tag = self.tag

        def lazy_load_action_structure(sender: str, anchor: str, action: Action):
            entrypoint = bnk[action.target_id]
            self.on_node_selected(sender, None, entrypoint)
            g = bnk.get_hierarchy(entrypoint)

            def delve(nid: int) -> None:
                node: Node = bnk[nid]
                label = f"{node.type} ({node.id})"
                children = g.successors(nid)

                if children:
                    with table_tree_node(
                        label,
                        callback=self.on_node_selected,
                        table=f"{tag}_events_table",
                        tag=f"{tag}_node_{nid}",
                        before=anchor,
                        user_data=nid,
                    ):
                        for child_id in children:
                            delve(child_id)
                else:
                    with table_tree_leaf(
                        table=f"{tag}_events_table",
                        tag=f"{tag}_node_{nid}",
                        before=anchor,
                    ):
                        dpg.add_selectable(
                            label=label,
                            callback=self.on_node_selected,
                            tag=f"{tag}_node_{node.id}",
                            user_data=nid,
                        )

            delve(entrypoint.id)

        events = list(bnk.query({"type": "Event"}))
        dpg.set_value(
            f"{tag}_events_count",
            f"Showing {min(self.max_events, len(events))}/{len(events)} events",
        )

        for node in events:
            event = Event(node.dict)

            # TODO make this filter configurable
            for aid in event.actions:
                action = Action(bnk[aid].dict)
                if action.action_type == ActionType.PLAY:
                    break
            else:
                # Not a play action
                continue

            self.events[event.id] = event
            name = event.lookup_name("<?>")

            with table_tree_node(
                f"{name} ({event.id})",
                callback=self.on_node_selected,
                table=f"{tag}_events_table",
                tag=f"{tag}_event_{event.id}",
                user_data=event,
            ):
                for aid in event.actions:
                    action = Action(bnk[aid].dict)
                    add_lazy_table_tree_node(
                        f"{action.action_type.name} ({aid})",
                        lazy_load_action_structure,
                        table=f"{tag}_events_table",
                        tag=f"{tag}_action_{aid}",
                        user_data=action,
                    )
            
            if len(self.events) >= self.max_events:
                break

        logger.info(f"Loaded {len(self.events)} events")

    def on_node_selected(self, sender: str, app_data: Any, node: int | Node) -> None:
        if isinstance(node, int):
            node: Node = self.bnk[node]

        node = node.cast()
        dpg.set_value(f"{self.tag}_json", node.json())
        # TODO update attributes window

    def clear(self) -> None:
        self.bnk = None
        self.events.clear()

        tag = self.tag
        dpg.delete_item(f"{tag}_events_table", children_only=True, slot=1)
        dpg.delete_item(f"{tag}_attributes", children_only=True, slot=1)
        dpg.set_value(f"{tag}_json", "")
        dpg.set_value(f"{tag}_events_filter", "")


if __name__ == "__main__":
    dpg.create_context()
    dpg_init()
    dpg.create_viewport(title="PyBnk", width=600, height=600)

    with dpg.window() as main_window:
        app = PyBnkGui()

    dpg.set_primary_window(main_window, True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
