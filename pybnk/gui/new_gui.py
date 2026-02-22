from typing import Any
from importlib import resources
import json
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.types import Action, Event
from pybnk.util import logger, unpack_soundbank, repack_soundbank
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
        self.max_events = 500
        self.language: Localization = English()
        self.bnk: Soundbank = None
        self.events: dict[int, Event] = {}
        self.selected_node: Node = None

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
                    callback=self._save_soundbank,
                )
                dpg.add_menu_item(
                    label="Save As...",
                    shortcut="ctrl-shift-s",
                    callback=self._save_soundbank_as,
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Repack",
                    shortcut="f4",
                    callback=self._repack_soundbank,
                )

            with dpg.menu(label="Help"):
                with dpg.menu(label="dearpygui"):
                    dpg.add_menu_item(
                        label="About", callback=lambda: dpg.show_tool(dpg.mvTool_About)
                    )
                    dpg.add_menu_item(
                        label="Metrics", callback=lambda: dpg.show_tool(dpg.mvTool_Metrics)
                    )
                    dpg.add_menu_item(
                        label="Documentation",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Doc),
                    )
                    dpg.add_menu_item(
                        label="Debug", callback=lambda: dpg.show_tool(dpg.mvTool_Debug)
                    )
                    dpg.add_menu_item(
                        label="Style Editor",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Style),
                    )
                    dpg.add_menu_item(
                        label="Font Manager",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Font),
                    )
                    dpg.add_menu_item(
                        label="Item Registry",
                        callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry),
                    )
                    dpg.add_menu_item(
                        label="Stack Tool",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Stack),
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
                dpg.add_input_text(
                    hint="Filter...", width=-1, tag=f"{tag}_events_filter"
                )
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

            dpg.add_child_window(
                autosize_y=True,
                width=400,
                resizable_x=True,
                border=True,
                tag=f"{tag}_attributes",
            )

            with dpg.child_window(
                width=400,
                autosize_x=True,
                autosize_y=True,
                border=False,
            ):
                dpg.add_input_text(
                    multiline=True,
                    width=-1,
                    height=-30,
                    callback=None,  # TODO change border color to show changes were made
                    tag=f"{tag}_json",
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Apply",
                        callback=self.apply_json,
                    )
                    dpg.add_button(
                        label="Reset",
                        callback=self.reset_json,
                    )

    def _save_soundbank(self) -> None:
        if not self.bnk:
            return

        self.bnk.save()

    def _save_soundbank_as(self) -> None:
        if not self.bnk:
            return

        lang = self.language
        path = save_file_dialog(
            title=lang.save_soundbank,
            default_dir=str(self.bnk.bnk_dir),
            filetypes={lang.json_files: "*.json"},
        )
        if path:
            self.bnk.save(path)

    def _repack_soundbank(self) -> None:
        if not self.bnk:
            return

        repack_soundbank(self.bnk.bnk_dir)

    def _open_soundbank(self) -> None:
        lang = self.language
        path = open_file_dialog(
            title=lang.open,
            filetypes={
                lang.json_files: "*.json",
                lang.soundbank_files: "*.bnk",
            },
        )
        if path:
            if path.endswith(".bnk"):
                unpack_soundbank(path)
            self._load_soundbank(path)

    def _load_soundbank(self, path: str) -> None:
        logger.info(f"Loading soundbank {path}")
        bnk = Soundbank.load(path)

        self.clear()
        self.bnk = bnk
        tag = self.tag

        def node_selected_helper(sender: str, app_data: Any, node: Node) -> None:
            self.on_node_selected(node)

        def lazy_load_action_structure(
            sender: str, anchor: str, action: Action
        ) -> None:
            node_selected_helper(sender, None, action)

            entrypoint = bnk[action.target_id]
            g = bnk.get_hierarchy(entrypoint)

            def delve(nid: int) -> None:
                node: Node = bnk[nid]
                label = f"{node.type} ({node.id})"
                children = g.successors(nid)

                if children:
                    with table_tree_node(
                        label,
                        callback=node_selected_helper,
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
                            callback=node_selected_helper,
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
                callback=node_selected_helper,
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

    def regenerate(self) -> None:
        if self.selected_node:
            self.on_node_selected(self.selected_node)

    def apply_json(self) -> None:
        if not self.selected_node:
            return

        data_str = dpg.get_value(f"{self.tag}_json")
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse json", exc_info=e)
            # TODO show error to user
            return

        self.selected_node.update(data)
        self.regenerate()

    def reset_json(self) -> None:
        value = ""
        if self.selected_node:
            value = self.selected_node.json()
        dpg.set_value(f"{self.tag}_json", value)

    def on_node_selected(self, node: int | Node) -> None:
        if isinstance(node, int):
            node: Node = self.bnk[node]

        node = node.cast()
        self.selected_node = node

        dpg.set_value(f"{self.tag}_json", node.json())
        self._create_attribute_widgets()

    def _create_attribute_widgets(self) -> None:
        dpg.delete_item(f"{self.tag}_attributes", children_only=True, slot=1)
        node = self.selected_node

        if not node:
            return

        def update_name_and_id(sender: str, new_name: str, user_data: Any) -> None:
            if not new_name:
                return

            node.id = new_name
            dpg.set_value(f"{self.tag}_attr_hash", str(node.id))

        with dpg.group(parent=f"{self.tag}_attributes"):
            dpg.add_text(node.type)
            dpg.add_input_text(
                label="Name", 
                default_value=node.lookup_name("<?>"),
                callback=update_name_and_id,
            )
            dpg.add_input_text(
                label="Hash",
                default_value=str(node.id),
                readonly=True,
                enabled=False,
                tag=f"{self.tag}_attr_hash",
            )

            properties = {
                name: prop
                for name, prop in node.__class__.__dict__.items()
                if isinstance(prop, property)
            }

            for name, prop in properties.items():
                value = prop.fget(node)
                readonly = prop.fset is None

                def set_property(sender: str, new_value: Any, prop: property):
                    prop.fset(node, new_value)

                if isinstance(value, bool):
                    dpg.add_checkbox(
                        label=name,
                        default_value=value,
                        callback=set_property,
                        enabled=not readonly,
                        user_data=prop,
                    )
                elif isinstance(value, int):
                    dpg.add_input_int(
                        label=name,
                        default_value=value,
                        callback=set_property,
                        readonly=readonly,
                        enabled=not readonly,
                        user_data=prop,
                    )
                elif isinstance(value, float):
                    dpg.add_input_float(
                        label=name,
                        default_value=value,
                        callback=set_property,
                        readonly=readonly,
                        enabled=not readonly,
                        user_data=prop,
                    )
                elif isinstance(value, str):
                    dpg.add_input_text(
                        label=name,
                        default_value=value,
                        callback=set_property,
                        readonly=readonly,
                        enabled=not readonly,
                        user_data=prop,
                    )

            dpg.add_child_window(height=-30, border=False)
            dpg.add_button(label="Reset")

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
    dpg.create_viewport(title="PyBnk", width=1000, height=700)

    with dpg.window() as main_window:
        app = PyBnkGui()

    dpg.set_primary_window(main_window, True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
