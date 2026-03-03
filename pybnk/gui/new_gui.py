from typing import Any, Type
import sys
from importlib import resources
import logging
import json
from pathlib import Path
from collections import deque
import pyperclip
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.types import WwiseNode, Action, Event
from pybnk.util import logger, unpack_soundbank, repack_soundbank
from pybnk.enums import ActionType
from pybnk.gui.config import Config, load_config
from pybnk.gui.helpers import create_widget, center_window, create_properties_table
from pybnk.gui import style
from pybnk.gui.style import init_themes, themes
from pybnk.gui.localization import Localization, English
from pybnk.gui.table_tree_nodes import (
    table_tree_node,
    table_tree_leaf,
    add_lazy_table_tree_node,
    set_foldable_row_status,
)
from pybnk.gui.dialogs.create_node_dialog import create_node_dialog
from pybnk.gui.dialogs.new_wwise_event_dialog import new_wwise_event_dialog
from pybnk.gui.dialogs.file_dialog import open_file_dialog, save_file_dialog
from pybnk.gui.dialogs.create_simple_sound_dialog import create_simple_sound_dialog
from pybnk.gui.dialogs.calc_hash_dialog import calc_hash_dialog


# TODO filters
# TODO boss music
# TODO ambience
# TODO mass transfer
# TODO convert audio files
# TODO edit globals (buses, actor mixers, attenuations)
# TODO setup RTCPs
# TODO streaming audio
# TODO action graph visualization
# TODO localizations


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
        self.max_list_nodes = 500
        self.language: Localization = English()
        self.bnk: Soundbank = None
        self.event_map: dict[int, Event] = {}
        self.globals_map: dict[int, Event] = {}
        self._selected_root: str = None
        self._selected_node: Node = None
        self._selected_node_backup: str = None

        self.config: Config = load_config()

        self._setup_menu()
        self._setup_content()
        self._setup_context_menus()

        class LogHandler(logging.Handler):
            def emit(this, record: logging.LogRecord):
                if record.levelno >= logging.ERROR:
                    color = style.red
                elif record.levelno >= logging.WARNING:
                    color = style.yellow
                else:
                    color = style.blue

                self.show_notification(record.message, color)

        sys.excepthook = self._handle_exception
        logger.addHandler(LogHandler())

    def _handle_exception(
        self, exc_type: Type[Exception], exc_value: Exception, exc_traceback
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            dpg.stop_dearpygui()
            return

        self.show_notification(str(exc_value), style.red)
        raise exc_value

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
                    tag=f"{self.tag}_menu_file_save",
                )
                dpg.add_menu_item(
                    label="Save As...",
                    shortcut="ctrl-shift-s",
                    callback=self._save_soundbank_as,
                    tag=f"{self.tag}_menu_file_save_as",
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Repack",
                    shortcut="f4",
                    callback=self._repack_soundbank,
                    tag=f"{self.tag}_menu_file_repack",
                )

            with dpg.menu(label="Soundbank", tag=f"{self.tag}_menu_edit"):
                dpg.add_menu_item(
                    label="Delete orphans",
                    callback=self._bank_delete_orphans,
                )

            with dpg.menu(label="Create", tag=f"{self.tag}_menu_create"):
                dpg.add_menu_item(
                    label="New Wwise Event",
                    callback=self._open_new_wwise_event_dialog,
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Simple Sound",
                    callback=self._open_simple_sound_dialog,
                )
                dpg.add_menu_item(
                    label="Boss Track",
                    callback=self._open_boss_track_dialog,
                    enabled=False,  # TODO
                )
                dpg.add_menu_item(
                    label="Ambience Track",
                    callback=self._open_ambience_track_dialog,
                    enabled=False,  # TODO
                )

            with dpg.menu(label="Tools"):
                dpg.add_menu_item(
                    label="Calc Hash",
                    callback=self._open_calc_hash_dialog,
                )
                dpg.add_menu_item(
                    label="Mass Transfer",
                    callback=None,  # TODO self._open_mass_transfer_dialog,
                )
                dpg.add_menu_item(
                    label="Convert Audio Files",
                    callback=None,  # TODO self._open_convert_audio_files_dialog,
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

    def _activate_bnk_menus(self, enabled: bool) -> None:
        for subtag in [
            "_menu_file_save",
            "_menu_file_save_as",
            "_menu_file_repack",
            "_menu_edit",
            "_menu_create",
        ]:
            if enabled:
                dpg.enable_item(f"{self.tag}{subtag}")
            else:
                dpg.disable_item(f"{self.tag}{subtag}")

    def _setup_content(self) -> None:
        tag = self.tag

        def filter_events(sender: str, filt: str, user_data: Any) -> None:
            self._regenerate_events_list(filt)

        def filter_globals(sender: str, filt: str, user_data: Any) -> None:
            self._regenerate_globals_list(filt)

        with dpg.group(horizontal=True):
            with dpg.child_window(
                horizontal_scrollbar=False,
                width=300,
                resizable_x=True,
                autosize_y=True,
                tag=f"{tag}_events_window",
            ):
                with dpg.tab_bar():
                    with dpg.tab(label="Play"):
                        dpg.add_input_text(
                            hint="Filter...",
                            width=-1,
                            callback=filter_events,
                            tag=f"{tag}_events_filter",
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
                    with dpg.tab(label="Globals"):
                        dpg.add_input_text(
                            hint="Filter...",
                            width=-1,
                            callback=filter_globals,
                            tag=f"{tag}_globals_filter",
                        )
                        dpg.add_text("Showing 0 globals", tag=f"{tag}_globals_count")
                        with dpg.table(
                            no_host_extendX=True,
                            resizable=True,
                            borders_innerV=True,
                            policy=dpg.mvTable_SizingFixedFit,
                            header_row=False,
                            tag=f"{tag}_globals_table",
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

        with dpg.window(
            no_title_bar=True,
            no_move=True,
            no_close=True,
            no_saved_settings=True,
            show=False,
            min_size=(10, 10),
            tag=f"{tag}_notification_window",
        ):
            with dpg.group(width=-1):
                dpg.add_text("TEST", color=style.red, tag=f"{tag}_notification_text")

        dpg.bind_item_theme(f"{tag}_notification_window", themes.notification_frame)

        with dpg.handler_registry():
            dpg.add_mouse_click_handler(
                callback=lambda s, a, u: dpg.hide_item(f"{tag}_notification_window")
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
                label="New child",
                callback=self.node_new_child,
                tag=f"{tag}_context_new_child",
            )
            with dpg.menu(label="Add action", tag=f"{tag}_context_add_action"):
                dpg.add_menu_item(
                    label="Play",
                    callback=self.node_add_action_play,
                    tag=f"{tag}_context_add_action_play",
                )
                dpg.add_menu_item(
                    label="Stop",
                    callback=self.node_add_action_stop,
                    tag=f"{tag}_context_add_action_stop",
                )
                dpg.add_menu_item(
                    label="Mute Bus",
                    callback=self.node_add_action_mute_bus,
                    tag=f"{tag}_context_add_action_mute_bus",
                )
                dpg.add_menu_item(
                    label="Reset Bus Volume",
                    callback=self.node_add_action_reset_bus_volume,
                    tag=f"{tag}_context_add_action_reset_bus",
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
            # TODO copy/paste hierarchy
            dpg.add_separator()
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

    def show_notification(
        self, msg: str, color: tuple[int, int, int, int] = style.red
    ) -> None:
        w = dpg.get_viewport_width() - 6
        h = dpg.get_viewport_height() - dpg.get_item_height(
            f"{self.tag}_notification_window"
        )
        # Note: since this is a popup there's no need for a timer to hide it
        dpg.configure_item(
            f"{self.tag}_notification_window", show=True, pos=(-5, h), min_size=(w, 10)
        )
        dpg.configure_item(
            f"{self.tag}_notification_text", default_value=msg, color=color
        )

    def _set_component_highlight(self, widget: str, highlight: bool) -> None:
        if highlight:
            dpg.bind_item_theme(widget, themes.item_blue)
        else:
            dpg.bind_item_theme(widget, themes.item_default)

    def locate_bnk2json(self) -> str:
        if not self.config.bnk2json_exe or not Path(self.config.bnk2json_exe).is_file():
            bnk2json_exe = open_file_dialog(
                title="Locate bnk2json.exe", filetypes={"bnk2json": "bnk2json.exe"}
            )
            if not bnk2json_exe:
                raise ValueError("bnk2json is required for (re-)packing soundbanks")

            self.config.bnk2json_exe = bnk2json_exe
            self.config.save()

        return self.config.bnk2json_exe

    def locate_wwise(self) -> str:
        if not self.config.wwise_exe or not Path(self.config.wwise_exe).is_file():
            wwise_exe = open_file_dialog(
                title="Locate WwiseConsole.exe",
                filetypes={"WwiseConsole": "WwiseConsole.exe"},
            )
            if not wwise_exe:
                raise ValueError("WwiseConsole is required for converting to WEM")

            self.config.wwise_exe = wwise_exe
            self.config.save()

        return self.config.wwise_exe

    def locate_vgmstream(self) -> str:
        if (
            not self.config.vgmstream_exe
            or not Path(self.config.vgmstream_exe).is_file()
        ):
            vgmstream_exe = open_file_dialog(
                title="Locate vgmstream-cli.exe",
                filetypes={"vgmstream-cli": "vgmstream-cli.exe"},
            )
            if not vgmstream_exe:
                raise ValueError("vgmstream-cli is required for converting WEMs")

            self.config.vgmstream_exe = vgmstream_exe
            self.config.save()

        return self.config.wwise_exe

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

        bnk2json = self.locate_bnk2json()
        repack_soundbank(bnk2json, self.bnk.bnk_dir)

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
                bnk2json = self.locate_bnk2json()
                unpack_soundbank(bnk2json, path)

            self._load_soundbank(path)
            self._activate_bnk_menus(True)
            self.config.add_recent_file(path)
            self.config.save()

    def _load_soundbank(self, path: str) -> None:
        logger.info(f"Loading soundbank {path}")
        self.bnk = Soundbank.load(path)
        self.regenerate()
        logger.info(f"Loaded {len(self.event_map)} events")

    def _create_root_entry(self, node: Event, table: str) -> None:
        bnk = self.bnk

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

                sub_tag = f"{table}_node_{nid}"
                if dpg.does_item_exist(sub_tag):
                    # Item already open somewhere else
                    label = f"*{node.type} ({node.id})"
                    with table_tree_leaf(
                        table=table,
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
                        table=table,
                        tag=sub_tag,
                        before=anchor,
                        user_data=nid,
                    ) as row:
                        register_context_menu(row.selectable, node)
                        for child_id in children:
                            delve(child_id)
                else:
                    with table_tree_leaf(
                        table=table,
                        tag=sub_tag,
                        before=anchor,
                    ) as row:
                        register_context_menu(row.selectable, node)
                        dpg.add_selectable(
                            label=label,
                            callback=self._on_node_selected,
                            tag=f"{table}_node_{node.id}",
                            user_data=nid,
                        )

            delve(entrypoint.id)

        with table_tree_node(
            str(node),
            on_click_callback=self._on_node_selected,
            table=table,
            tag=f"{table}_node_{node.id}",
            user_data=node,
        ) as root_row:
            register_context_menu(root_row.selectable, node)
            for _, ref_id in node.get_references():
                child = bnk[ref_id]
                child_row = add_lazy_table_tree_node(
                    str(child),
                    lazy_load_action_structure,
                    on_click_callback=self._on_node_selected,
                    table=table,
                    tag=f"{table}_node_{node.id}_{ref_id}",
                    user_data=child,
                )
                register_context_menu(child_row.selectable, child)

    def regenerate(self) -> None:
        self.clear()
        self._regenerate_events_list()
        self._regenerate_globals_list()

    def _regenerate_events_list(self, filt: str = None) -> None:
        self.event_map.clear()
        events = list(self.bnk.query(f"type=Event {filt or ''}"))
        dpg.set_value(
            f"{self.tag}_events_count",
            f"Showing {min(self.max_list_nodes, len(events))}/{len(events)} events",
        )

        for node in events:
            node: Event = node.cast()

            # TODO make this filter configurable
            for aid in node.actions:
                action = Action(self.bnk[aid].dict)
                if action.action_type == ActionType.PLAY:
                    break
            else:
                # Not a play action
                continue

            node_tag = self._create_root_entry(node, f"{self.tag}_events_table")
            self.event_map[node.id] = node_tag
            if len(self.event_map) >= self.max_list_nodes:
                break

    def _regenerate_globals_list(self, filt: str = None) -> None:
        # TODO filter
        self.globals_map.clear()
        global_nodes = [
            n
            for n in self.bnk.hirc
            if n.parent is None and n.type not in ("Event", "Action")
        ]
        dpg.set_value(
            f"{self.tag}_globals_count",
            f"Showing {min(self.max_list_nodes, len(global_nodes))}/{len(global_nodes)} globals",
        )

        type_map: dict[str, list[Node]] = {}
        for node in global_nodes:
            type_map.setdefault(node.type, []).append(node)

        for node_type, nodes in type_map.items():
            with table_tree_node(
                node_type,
                table=f"{self.tag}_globals_table",
                on_click_callback=self._on_node_selected,
            ):
                for node in nodes:
                    node = node.cast()
                    node_tag = self._create_root_entry(
                        node, f"{self.tag}_globals_table"
                    )
                    self.globals_map[node.id] = node_tag
                    if len(self.globals_map) >= self.max_list_nodes:
                        break

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

        if isinstance(node, Event):
            dpg.show_item(f"{self.tag}_context_add_action")
        else:
            dpg.hide_item(f"{self.tag}_context_add_action")

        dpg.set_item_pos(f"{self.tag}_context_menu", dpg.get_mouse_pos())
        dpg.show_item(f"{self.tag}_context_menu")

    def select_node(self, node: int | Node) -> None:
        self._on_node_selected(None, None, node)

    def _on_node_selected(self, sender: str, app_data: Any, node: int | Node) -> None:
        # Deselect previous selectable
        if self._selected_root and dpg.does_item_exist(self._selected_root):
            dpg.set_value(self._selected_root, False)

        self._selected_root = sender
        if sender is not None:
            dpg.set_value(sender, True)

        if isinstance(node, int):
            node: Node = self.bnk[node]

        if isinstance(node, Node):
            node = node.cast()
            data = node.json()
            self._selected_node_backup = data
            dpg.set_value(f"{self.tag}_json", data)
        else:
            self._selected_node_backup = None
            dpg.set_value(f"{self.tag}_json", "")

        self._selected_node = node
        self._set_component_highlight(f"{self.tag}_json", False)
        self._create_attribute_widgets()

    def _create_attribute_widgets(self) -> None:
        dpg.delete_item(f"{self.tag}_attributes", children_only=True, slot=1)
        node = self._selected_node

        if not node:
            return

        def update_name_and_id(sender: str, new_name: str, user_data: Any) -> None:
            if not new_name:
                return

            node.id = new_name
            dpg.set_value(f"{self.tag}_attr_hash", str(node.id))

        def on_properties_changed(
            sender: str, properties: dict[str, float], node: WwiseNode
        ) -> None:
            for key, val in properties.items():
                node.set_property(key, val)

        with dpg.group(parent=f"{self.tag}_attributes"):
            # Heading
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

            # Find all exposed python properties, including those from base classes
            properties: dict[str, property] = {}
            todo = deque([node.__class__])
            while todo:
                c = todo.popleft()
                for name, prop in c.__dict__.items():
                    if name in ("id", "type", "parent"):
                        continue
                    if isinstance(prop, property):
                        properties.setdefault(name, prop)

                todo.extend(c.__bases__)

            for name, prop in properties.items():
                value_type = prop.fget.__annotations__["return"]
                value = prop.fget(node)
                readonly = prop.fset is None
                doc = doc_parse(prop.__doc__)

                def set_property(sender: str, new_value: Any, prop: property):
                    prop.fset(node, new_value)
                    self.update_json_panel()

                try:
                    widget = create_widget(
                        value_type,
                        name,
                        set_property,
                        default=value,
                        readonly=readonly,
                        user_data=prop,
                    )
                except Exception:
                    continue

                if widget and doc:
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(doc.short_description)

            if isinstance(node, WwiseNode):
                create_properties_table(
                    node.properties,
                    on_properties_changed,
                    user_data=node,
                )

            dpg.add_child_window(height=-30, border=False)
            dpg.add_button(label="Reset")

    def regenerate_attributes(self) -> None:
        self._on_node_selected(self._selected_root, True, self._selected_node)

    def clear(self) -> None:
        tag = self.tag
        dpg.set_value(f"{tag}_events_filter", "")
        dpg.delete_item(f"{tag}_events_table", children_only=True, slot=1)
        dpg.set_value(f"{tag}_globals_filter", "")
        dpg.delete_item(f"{tag}_globals_table", children_only=True, slot=1)
        dpg.delete_item(f"{tag}_attributes", children_only=True, slot=1)
        dpg.set_value(f"{tag}_json", "")

    def _bank_delete_orphans(self) -> None:
        self.bnk.delete_orphans()
        self.regenerate()

    def node_new_child(self) -> None:
        tag = f"{self.tag}_add_child_to_{self._selected_node.id}"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_node_created(node: WwiseNode) -> None:
            self.bnk.add_nodes(node)
            self._selected_node.add_child(node)
            logger.info(f"Attached new node {node} to {self._selected_node}")
            # TODO no need to regenerate everything
            self.regenerate()

        create_node_dialog(self.bnk, on_node_created, tag=tag)

        dpg.split_frame()
        center_window(tag)

    def node_add_action_play(self) -> None:
        act = Action.new_play_action(self.bnk.new_id(), 0)
        self._selected_node.add_action(act)
        self.bnk.add_nodes(act)
        self.regenerate()
        set_foldable_row_status(f"{self.tag}_event_{self._selected_node.id}", True)
        self.select_node(act)

    def node_add_action_stop(self) -> None:
        act = Action.new_stop_action(self.bnk.new_id(), 0)
        self._selected_node.add_action(act)
        self.bnk.add_nodes(act)
        self.regenerate()
        set_foldable_row_status(f"{self.tag}_event_{self._selected_node.id}", True)
        self.select_node(act)

    def node_add_action_mute_bus(self) -> None:
        act = Action.new_mute_bus_action(self.bnk.new_id(), 0)
        self._selected_node.add_action(act)
        self.bnk.add_nodes(act)
        self.regenerate()
        set_foldable_row_status(f"{self.tag}_event_{self._selected_node.id}", True)
        self.select_node(act)

    def node_add_action_reset_bus_volume(self) -> None:
        act = Action.new_reset_bus_volume_action(self.bnk.new_id(), 0)
        self._selected_node.add_action(act)
        self.bnk.add_nodes(act)
        self.regenerate()
        set_foldable_row_status(f"{self.tag}_event_{self._selected_node.id}", True)
        self.select_node(act)

    def node_cut(self) -> None:
        self.node_copy()
        self.node_delete()
        logger.info(f"Cut node {self._selected_node} to clipboard")
        self._on_node_selected(None, False, None)
        self.regenerate()

    def node_copy(self) -> None:
        data = self._selected_node.json()
        pyperclip.copy(data)
        logger.info(f"Copied node {self._selected_node} to clipboard")

    def node_paste_child(self) -> None:
        data = json.loads(pyperclip.paste())
        node = Node.wrap(data)
        if not isinstance(node, WwiseNode):
            raise ValueError(f"Node {node} cannot be parented")

        if node.id in self.bnk:
            node.id = self.bnk.new_id()
            logger.warning(
                f"ID of pasted node already exists, assigned new ID {node.id}"
            )

        self.bnk.add_nodes(node)
        self._selected_node.add_child(node)
        logger.info(
            f"Pasted node {node} from clipboard as child of {self._selected_node}"
        )
        self.regenerate()

    def node_delete(self) -> None:
        if not self._selected_node:
            return

        self.bnk.delete_nodes(self._selected_node)
        logger.info(f"Deleted node {self._selected_node} and all its children")
        self._on_node_selected(None, False, None)
        self.regenerate()

    def node_apply_json(self) -> None:
        if not self._selected_node:
            return

        data_str = dpg.get_value(f"{self.tag}_json")
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to parse json") from e

        self._selected_node.update(data)
        # TODO keep selected open
        self.regenerate()

    def node_reset_json(self) -> None:
        if self._selected_node:
            self._selected_node.update(self._selected_node_backup)
            self.update_json_panel()

    def update_json_panel(self) -> None:
        value = ""
        if self._selected_node:
            value = self._selected_node.json()
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

        create_node_dialog(self.bnk, on_node_created, tag=tag)

        dpg.split_frame()
        center_window(tag)

    def _open_new_wwise_event_dialog(self) -> None:
        tag = f"{self.tag}_new_wwise_event_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_events_created(nodes: list[Node]) -> None:
            logger.info(f"Created {len(nodes)} new nodes")
            self.regenerate()
            self.select_node(nodes[0])

        new_wwise_event_dialog(self.bnk, on_events_created, tag=tag)

        dpg.split_frame()
        center_window(tag)

    def _open_simple_sound_dialog(self) -> None:
        tag = f"{self.tag}_create_simple_sound_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        def on_sound_created(play_evt: Event, stop_evt: Event) -> None:
            logger.info(f"Added new sound {play_evt.lookup_name()} ({play_evt.id})")
            self.regenerate()

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
            logger.info(
                f"Added new boss track {nodes[0].lookup_name()} ({nodes[0].id})"
            )

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
            logger.info(
                f"Added new ambience track {nodes[0].lookup_name()} ({nodes[0].id})"
            )

        create_ambience_track_dialog(self.bnk, on_ambience_track_created, tag=tag)

        dpg.split_frame()
        center_window(tag)

    def _open_calc_hash_dialog(self) -> None:
        tag = f"{self.tag}_calc_hash_dialog"
        if dpg.does_item_exist(tag):
            dpg.show_item(tag)
            dpg.focus_item(tag)
            return

        calc_hash_dialog(tag=tag)

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
