from typing import Any
from importlib import resources
import json
import pyperclip
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

            with dpg.menu(label="Edit"):
                dpg.add_menu_item(
                    label="Delete orphans",
                    callback=self._bank_delete_orphans,
                )

            with dpg.menu(label="Create"):
                dpg.add_menu_item(
                    label="Simple Sound",
                    callback=self._open_simple_sound_dialog,
                )
                dpg.add_menu_item(
                    label="Boss Track",
                    callback=self._open_boss_track_dialog,
                )
                dpg.add_menu_item(
                    label="Ambience Track",
                    callback=self._open_ambience_track_dialog,
                )

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
                label="Cut",
                callback=self.node_cut,
                tag=f"{tag}_context_cut",
            )
            dpg.add_menu_item(
                label="Copy",
                callback=self.node_copy,
                tag=f"{tag}_context_copy",
            )
            dpg.add_separator()
            dpg.add_menu_item(
                label="New child",
                callback=self.node_new_child,
                tag=f"{tag}_context_new_child",
            )
            dpg.add_menu_item(
                label="Paste child",
                callback=self.node_paste_child,
                tag=f"{tag}_context_paste_child",
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
        self.bnk = Soundbank.load(path)
        self.regenerate()

    def _create_root_entry(self, event: Event) -> None:
        bnk = self.bnk
        tag = self.tag

        def register_context_menu(tag: str, node: Node) -> None:
            registry = f"{tag}_handlers"

            if not dpg.does_item_exist(registry):
                dpg.add_item_handler_registry(tag=registry)

            dpg.add_item_clicked_handler(
                dpg.mvMouseButton_Right,
                callback=self._open_context_menu,
                user_data=(tag, node),
                parent=registry,
            )
            dpg.bind_item_handler_registry(tag, registry)

        def lazy_load_action_structure(
            sender: str, anchor: str, action: Action
        ) -> None:
            entrypoint = bnk[action.target_id]
            g = bnk.get_subtree(entrypoint)

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
                            callback=self._on_node_selected,  # TODO navigate to other instance?
                            user_data=nid,
                        )

                    return

                label = f"{node.type} ({node.id})"
                children = g.successors(nid)

                if children:
                    with table_tree_node(
                        label,
                        on_click_callback=self._on_node_selected,
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
                            callback=self._on_node_selected,
                            tag=f"{tag}_node_{node.id}",
                            user_data=nid,
                        )

            delve(entrypoint.id)

        self.events[event.id] = event
        name = event.lookup_name("<?>")

        with table_tree_node(
            f"{name} ({event.id})",
            on_click_callback=self._on_node_selected,
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
                    on_click_callback=self._on_node_selected,
                    table=f"{tag}_events_table",
                    tag=f"{tag}_action_{aid}",
                    user_data=action,
                )
                register_context_menu(action_row.selectable, action)

    def regenerate(self) -> None:
        self.clear()
        self.events.clear()
        
        events = list(self.bnk.query({"type": "Event"}))
        dpg.set_value(
            f"{self.tag}_events_count",
            f"Showing {min(self.max_events, len(events))}/{len(events)} events",
        )

        for node in events:
            event = Event(node.dict)

            # TODO make this filter configurable
            for aid in event.actions:
                action = Action(self.bnk[aid].dict)
                if action.action_type == ActionType.PLAY:
                    break
            else:
                # Not a play action
                continue
            
            self._create_root_entry(event)
            if len(self.events) >= self.max_events:
                break

        logger.info(f"Loaded {len(self.events)} events")

    def _open_context_menu(
        self, sender: str, app_data: Any, user_data: tuple[str, Node]
    ) -> None:
        item, node = user_data
        self._on_node_selected(item, app_data, node)

        if "children" in node:
            dpg.show_item(f"{self.tag}_context_new_child")
            dpg.show_item(f"{self.tag}_context_paste_child")
        else:
            dpg.hide_item(f"{self.tag}_context_new_child")
            dpg.hide_item(f"{self.tag}_context_paste_child")

        dpg.set_item_pos(f"{self.tag}_context_menu", dpg.get_mouse_pos())
        dpg.show_item(f"{self.tag}_context_menu")

    def _on_node_selected(self, sender: str, app_data: Any, node: int | Node) -> None:
        # Deselect previous selectable
        if self.selected_root and dpg.does_item_exist(self.selected_root):
            dpg.set_value(self.selected_root, False)

        self.selected_root = sender
        if sender is not None:
            dpg.set_value(sender, True)

        if isinstance(node, int):
            node: Node = self.bnk[node]

        if isinstance(node, Node):
            node = node.cast()
            dpg.set_value(f"{self.tag}_json", node.json())

        self.selected_node = node
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
            if node.type == "Event":
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

    def regenerate_attributes(self) -> None:
        self._on_node_selected(self.selected_root, True, self.selected_node)
    
    def clear(self) -> None:
        tag = self.tag
        dpg.delete_item(f"{tag}_events_table", children_only=True, slot=1)
        dpg.delete_item(f"{tag}_attributes", children_only=True, slot=1)
        dpg.set_value(f"{tag}_json", "")
        dpg.set_value(f"{tag}_events_filter", "")

    def _bank_delete_orphans(self) -> None:
        self.bnk.delete_orphans()
        self.regenerate()

    def node_new_child(self) -> None:
        tag = f"{self.tag}_add_child_to_{self.selected_node.id}"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_node_created(node: WwiseNode) -> None:
            self.bnk.add_nodes(node)
            self.selected_node.add_child(node)
            logger.info(f"Attached new node {node} to {self.selected_node}")
            # TODO no need to regenerate everything
            self.regenerate()

        create_node_dialog(self.bnk, on_node_created, tag=tag)

        dpg.split_frame()
        center_window(tag)
    
    def node_cut(self) -> None:
        # TODO copy hierarchy?
        self.node_copy()
        self.node_delete()
        logger.info(f"Cut node {self.selected_node} to clipboard")
        self._on_node_selected(None, False, None)
        self.regenerate()
    
    def node_copy(self) -> None:
        # TODO copy hierarchy?
        data = self.selected_node.json()
        pyperclip.copy(data)
        logger.info(f"Copied node {self.selected_node} to clipboard")
    
    def node_paste_child(self) -> None:
        data = json.loads(pyperclip.paste())
        node = Node.wrap(data)
        if not isinstance(node, WwiseNode):
            raise ValueError(f"Node {node} cannot be parented")

        if node.id in self.bnk:
            node.id = self.bnk.new_id()
            logger.warning(f"ID of pasted node already exists, assigned new ID {node.id}")
        
        self.bnk.add_nodes(node)
        self.selected_node.add_child(node)
        logger.info(f"Pasted node {node} from clipboard as child of {self.selected_node}")
        self.regenerate()
    
    def node_delete(self) -> None:
        if not self.selected_node:
            return

        self.bnk.delete_nodes(self.selected_node)
        logger.info(f"Deleted node {self.selected_node} and all its children")
        self._on_node_selected(None, False, None)
        self.regenerate()
    
    def node_apply_json(self) -> None:
        if not self.selected_node:
            return

        data_str = dpg.get_value(f"{self.tag}_json")
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse json", exc_info=e)
            # TODO show error to user, statusbar?
            
            return

        self.selected_node.update(data)
        # TODO might have new/different references, regenerate all children
        self.regenerate_attributes()

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
            data = node.json()
            pyperclip.copy(data)
            logger.info(f"Copied new node {node} to clipboard")
            # TODO notify user
            # TODO add to soundbank?

        create_node_dialog(self.bnk, on_node_created, tag=tag)

        dpg.split_frame()
        center_window(tag)

    def _open_simple_sound_dialog(self) -> None:
        tag = f"{self.tag}_create_simple_sound_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_sound_created(nodes: list[Node]) -> None:
            self.bnk.add_nodes(nodes)
            logger.info(f"Added new sound {nodes[0].lookup_name()} ({nodes[0].id})")

        create_simple_sound_dialog(self.bnk, on_sound_created, tag=tag)

        dpg.split_frame()
        center_window(tag)
    
    def _open_boss_track_dialog(self) -> None:
        tag = f"{self.tag}_create_boss_track_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_boss_track_created(nodes: list[Node]) -> None:
            self.bnk.add_nodes(nodes)
            logger.info(f"Added new boss track {nodes[0].lookup_name()} ({nodes[0].id})")

        create_boss_track_dialog(self.bnk, on_boss_track_created, tag=tag)

        dpg.split_frame()
        center_window(tag)
    
    def _open_ambience_track_dialog(self) -> None:
        tag = f"{self.tag}_create_ambience_track_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_ambience_track_created(nodes: list[Node]) -> None:
            self.bnk.add_nodes(nodes)
            logger.info(f"Added new ambience track {nodes[0].lookup_name()} ({nodes[0].id})")

        create_ambience_track_dialog(self.bnk, on_ambience_track_created, tag=tag)

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
