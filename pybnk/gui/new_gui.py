from typing import Any
from importlib import resources
import json
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.types import WwiseNode, Action, Event
from pybnk.util import logger, unpack_soundbank, repack_soundbank
from pybnk.enums import ActionType
from pybnk.gui.helpers import create_widget, center_window
from pybnk.gui.style import init_themes, themes
from pybnk.gui.file_dialog import open_file_dialog, save_file_dialog
from pybnk.gui.localization import Localization, English
from pybnk.gui.table_tree_nodes import (
    table_tree_node,
    table_tree_leaf,
    add_lazy_table_tree_node,
)
from pybnk.gui.create_node_dialog import create_node_dialog


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
        self.selected_root: str = None

        self._setup_menu()
        self._setup_content()
        self._setup_context_menus()

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

            with dpg.menu(label="Create"):
                dpg.add_menu_item(
                    label="Simple Sound",
                    callback=None,  # TODO
                )
                dpg.add_menu_item(
                    label="Boss Track",
                    callback=None,  # TODO
                )
                dpg.add_menu_item(
                    label="Ambience Track",
                    callback=None,  # TODO
                )

            with dpg.menu(label="Globals"):
                pass

            with dpg.menu(label="Help"):
                with dpg.menu(label="dearpygui"):
                    dpg.add_menu_item(
                        label="About", callback=lambda: dpg.show_tool(dpg.mvTool_About)
                    )
                    dpg.add_menu_item(
                        label="Metrics",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Metrics),
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
                width=300,
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
                    callback=lambda s, a, u: self._set_component_highlight(s, True),
                    tag=f"{tag}_json",
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Apply",
                        callback=self.node_apply_json,
                    )
                    dpg.add_button(
                        label="Reset",
                        callback=self.node_reset_json,
                    )

    def _setup_context_menus(self) -> None:
        tag = self.tag

        with dpg.window(
            popup=True,
            show=False,
            min_size=(50, 20),
            tag=f"{tag}_context_menu",
        ):
            dpg.add_menu_item(
                label="Add child",
                callback=self.node_add_child,
                tag=f"{tag}_context_add_child",
            )
            dpg.add_separator()
            dpg.add_menu_item(
                label="Cut",
                callback=self.node_cut,
                tag=f"{tag}_context_cut",
            )
            dpg.add_menu_item(
                label="Copy",
                callback=self.node_copy,
                tag=f"{tag}_context_copy",
            )
            dpg.add_menu_item(
                label="Paste",
                callback=self.node_paste,
                tag=f"{tag}_context_paste",
            )
            dpg.add_separator()
            dpg.add_menu_item(
                label="Delete",
                callback=self.node_delete,
                tag=f"{tag}_context_delete",
            )

    def _set_component_highlight(self, widget: str, highlight: bool) -> None:
        if highlight:
            dpg.bind_item_theme(widget, themes.item_blue)
        else:
            dpg.bind_item_theme(widget, themes.item_default)

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

        def register_context_menu(tag: str, node: Node) -> None:
            registry = f"{tag}_handlers"

            if not dpg.does_item_exist(registry):
                dpg.add_item_handler_registry(tag=registry)

            dpg.add_item_clicked_handler(
                dpg.mvMouseButton_Right,
                callback=self.open_context_menu,
                user_data=(tag, node),
                parent=registry,
            )
            dpg.bind_item_handler_registry(tag, registry)

        def lazy_load_action_structure(
            sender: str, anchor: str, action: Action
        ) -> None:
            entrypoint = bnk[action.target_id]
            g = bnk.get_hierarchy(entrypoint)

            def delve(nid: int) -> None:
                node: Node = bnk[nid]

                sub_tag = f"{tag}_node_{nid}"
                if dpg.does_item_exist(sub_tag):
                    # Item already open somewhere else
                    label = f"*{node.type} ({node.id})"
                    with table_tree_leaf(
                        table=f"{tag}_events_table",
                        before=anchor,
                    ) as row:
                        register_context_menu(row.selectable, node)
                        dpg.add_selectable(
                            label=label,
                            callback=self.on_node_selected,  # TODO navigate to other instance?
                            user_data=nid,
                        )

                    return

                label = f"{node.type} ({node.id})"
                children = g.successors(nid)

                if children:
                    with table_tree_node(
                        label,
                        on_click_callback=self.on_node_selected,
                        table=f"{tag}_events_table",
                        tag=sub_tag,
                        before=anchor,
                        user_data=nid,
                    ) as row:
                        register_context_menu(row.selectable, node)
                        for child_id in children:
                            delve(child_id)
                else:
                    with table_tree_leaf(
                        table=f"{tag}_events_table",
                        tag=sub_tag,
                        before=anchor,
                    ) as row:
                        register_context_menu(row.selectable, node)
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
                on_click_callback=self.on_node_selected,
                table=f"{tag}_events_table",
                tag=f"{tag}_event_{event.id}",
                user_data=event,
            ) as root_row:
                register_context_menu(root_row.selectable, event)
                for aid in event.actions:
                    # TODO Make actions the top level items and add a list of events associated with them?
                    action = Action(bnk[aid].dict)
                    action_row = add_lazy_table_tree_node(
                        f"{action.action_type.name} ({aid})",
                        lazy_load_action_structure,
                        on_click_callback=self.on_node_selected,
                        table=f"{tag}_events_table",
                        tag=f"{tag}_action_{aid}",
                        user_data=action,
                    )
                    register_context_menu(action_row.selectable, action)

            if len(self.events) >= self.max_events:
                break

        logger.info(f"Loaded {len(self.events)} events")

    def open_context_menu(
        self, sender: str, app_data: Any, user_data: tuple[str, Node]
    ) -> None:
        item, node = user_data
        self.on_node_selected(item, app_data, node)

        if "children" in node:
            dpg.show_item(f"{self.tag}_context_add_child")
        else:
            dpg.hide_item(f"{self.tag}_context_add_child")

        dpg.set_item_pos(f"{self.tag}_context_menu", dpg.get_mouse_pos())
        dpg.show_item(f"{self.tag}_context_menu")

    def on_node_selected(self, sender: str, app_data: Any, node: int | Node) -> None:
        # Deselect previous selectable
        if self.selected_root and dpg.does_item_exist(self.selected_root):
            dpg.set_value(self.selected_root, False)

        self.selected_root = sender
        dpg.set_value(sender, True)

        if isinstance(node, int):
            node: Node = self.bnk[node]

        node = node.cast()
        self.selected_node = node

        dpg.set_value(f"{self.tag}_json", node.json())
        self._set_component_highlight(f"{self.tag}_json", False)
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
                doc = doc_parse(prop.__doc__)

                def set_property(sender: str, new_value: Any, prop: property):
                    prop.fset(node, new_value)

                widget = create_widget(
                    type(value),
                    name,
                    set_property,
                    value,
                    readonly=readonly,
                    user_data=prop,
                )

                if widget and doc:
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(doc.short_description)

            dpg.add_child_window(height=-30, border=False)
            dpg.add_button(label="Reset")

    def regenerate(self) -> None:
        if self.selected_node:
            self.on_node_selected(self.selected_node)
    
    def clear(self) -> None:
        self.bnk = None
        self.events.clear()

        tag = self.tag
        dpg.delete_item(f"{tag}_events_table", children_only=True, slot=1)
        dpg.delete_item(f"{tag}_attributes", children_only=True, slot=1)
        dpg.set_value(f"{tag}_json", "")
        dpg.set_value(f"{tag}_events_filter", "")

    def node_add_child(sender: str, app_data: Any, user_data: Any) -> None:
        pass
    
    def node_cut(sender: str, app_data: Any, user_data: Any) -> None:
        pass
    
    def node_copy(sender: str, app_data: Any, user_data: Any) -> None:
        pass
    
    def node_paste(sender: str, app_data: Any, user_data: Any) -> None:
        pass
    
    def node_delete(sender: str, app_data: Any, user_data: Any) -> None:
        pass
    
    def node_apply_json(self) -> None:
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

    def node_reset_json(self) -> None:
        value = ""
        if self.selected_node:
            value = self.selected_node.json()
        dpg.set_value(f"{self.tag}_json", value)
        dpg.bind_item_theme(f"{self.tag}_json", themes.item_default)

    def _open_create_node_dialog(self) -> None:
        tag = f"{self.tag}_create_node_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_node_created(node: WwiseNode) -> None:
            print(node)
            pass

        create_node_dialog(self.bnk, on_node_created, tag=tag)

        dpg.split_frame()
        center_window(tag)


if __name__ == "__main__":
    dpg.create_context()
    dpg_init()
    init_themes()
    dpg.create_viewport(title="PyBnk", width=1100, height=700)

    with dpg.window() as main_window:
        app = PyBnkGui()

    dpg.set_primary_window(main_window, True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
