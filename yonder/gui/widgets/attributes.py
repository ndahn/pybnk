from typing import Any, Callable
from collections import deque
from pathlib import Path
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from yonder import Soundbank, Node
from yonder.hash import lookup_name
from yonder.node_types import (
    Action,
    ActorMixer,
    Attenuation,
    Bus,
    Event,
    LayerContainer,
    MusicRandomSequenceContainer,
    MusicSegment,
    MusicSwitchContainer,
    MusicTrack,
    RandomSequenceContainer,
    Sound,
    SwitchContainer,
    WwiseNode,
)
from yonder.util import logger
from yonder.gui import style
from yonder.gui.config import get_config
from .paragraphs import add_paragraphs
from .generic_input_widget import add_generic_widget
from .loading_indicator import loading_indicator
from .properties_table import add_properties_table
from .player_widget import add_wav_player
from .transition_matrix import add_transition_matrix


def create_attribute_widgets(
    bnk: Soundbank,
    node: Node,
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> str:
    if not tag:
        tag = dpg.generate_uuid()

    def update_node_name(sender: str, new_name: str, user_data: Any) -> None:
        if not new_name:
            return

        node.name = new_name
        dpg.set_value(f"{tag}_attr_hash", str(node.id))

    def on_node_properties_changed(
        sender: str, new_props: dict[str, float], node: WwiseNode
    ) -> None:
        for key in list(node.properties.keys()):
            if key not in new_props:
                node.remove_property(key)

        for key, val in new_props.items():
            node.set_property(key, val)

        on_node_changed(tag, node, user_data)

    def set_property(sender: str, new_value: Any, prop: property):
        prop.fset(node, new_value)
        on_node_changed(tag, node, user_data)

    loading = loading_indicator("loading...")
    try:
        with dpg.group(tag=tag, parent=parent):
            # Heading
            dpg.add_text(node.type)
            if node.__class__.__doc__:
                with dpg.tooltip(dpg.last_item()):
                    add_paragraphs(node.__class__.__doc__)

            if not isinstance(node, WwiseNode):
                dpg.add_input_text(
                    label="Name",
                    default_value=node.lookup_name("<?>"),
                    callback=update_node_name,
                )

            dpg.add_input_text(
                label="Hash",
                default_value=str(node.id),
                readonly=True,
                enabled=False,
                tag=f"{tag}_attr_hash",
            )

            dpg.add_spacer(height=3)
            dpg.add_separator()
            dpg.add_spacer(height=3)

            # Find all exposed python properties, including those from base classes
            properties: dict[str, property] = {}
            todo = deque([node.__class__])
            while todo:
                c = todo.popleft()
                for name, prop in c.__dict__.items():
                    if name in ("id", "name", "type", "parent"):
                        continue
                    if isinstance(prop, property):
                        properties.setdefault(name, prop)

                todo.extend(c.__bases__)

            # This may remove or add properties that are handled differently
            _create_type_specific_attributes(
                bnk,
                node,
                properties,
                on_node_changed,
                on_node_selected,
                tag=tag,
                parent=parent,
                user_data=user_data,
            )

            for name, prop in properties.items():
                value_type = prop.fget.__annotations__["return"]
                value = prop.fget(node)
                readonly = prop.fset is None
                doc = doc_parse(prop.__doc__)

                try:
                    widget = add_generic_widget(
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
                dpg.add_spacer(height=5)
                add_properties_table(
                    node.properties,
                    on_node_properties_changed,
                    user_data=node,
                )
    finally:
        dpg.delete_item(loading)

    return tag


def add_node_link(
    node: Node,
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    user_data: Any = None,
) -> str:
    if not tag:
        tag = dpg.generate_uuid()

    dpg.add_button(
        label=str(node),
        small=True,
        callback=lambda s, a, u: on_node_selected(tag, u, user_data),
        user_data=node,
        tag=tag,
    )
    dpg.bind_item_theme(dpg.last_item(), style.themes.link_button)
    return tag


def get_sound_path(bnk: Soundbank, source: dict) -> Path:
    source_id = source["media_information"]["source_id"]
    source_type = source["source_type"]

    wem = bnk.bnk_dir / f"{source_id}.wem"
    if source_type != "PrefetchStreaming" and wem.is_file():
        return wem

    # Find the largest external wem (if any)
    ext_wem = max(
        get_config().find_external_sounds(source_id, bnk),
        key=lambda p: p.stat().st_size,
        default=None,
    )
    if ext_wem:
        return ext_wem

    # In case we have a prefetch snippet but no streaming sound
    if wem.is_file() and source_type == "PrefetchStreaming":
        logger.warning(
            f"Could not find streamed sound for {source_id}, playing prefetch snippet"
        )
        return wem

    return None


def _create_type_specific_attributes(
    bnk: Soundbank,
    node: Node,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    if isinstance(node, Action):
        pass
    elif isinstance(node, ActorMixer):
        pass
    elif isinstance(node, Attenuation):
        pass
    elif isinstance(node, Bus):
        pass
    elif isinstance(node, Event):
        pass
    elif isinstance(node, LayerContainer):
        pass
    elif isinstance(node, MusicRandomSequenceContainer):
        _create_attributes_music_random_sequence_container(
            bnk,
            node,
            properties,
            on_node_changed,
            on_node_selected,
            tag=tag,
            parent=parent,
            user_data=user_data,
        )
    elif isinstance(node, MusicSegment):
        pass
    elif isinstance(node, MusicSwitchContainer):
        _create_attributes_music_switch_container(
            bnk,
            node,
            properties,
            on_node_changed,
            on_node_selected,
            tag=tag,
            parent=parent,
            user_data=user_data,
        )
    elif isinstance(node, MusicTrack):
        _create_attributes_music_track(
            bnk,
            node,
            properties,
            on_node_changed,
            on_node_selected,
            tag=tag,
            parent=parent,
            user_data=user_data,
        )
    elif isinstance(node, RandomSequenceContainer):
        pass
    elif isinstance(node, Sound):
        _create_attributes_sound(
            bnk,
            node,
            properties,
            on_node_changed,
            on_node_selected,
            tag=tag,
            parent=parent,
            user_data=user_data,
        )
    elif isinstance(node, SwitchContainer):
        _create_attributes_switch_container(
            bnk,
            node,
            properties,
            on_node_changed,
            on_node_selected,
            tag=tag,
            parent=parent,
            user_data=user_data,
        )


def _create_attributes_music_random_sequence_container(
    bnk: Soundbank,
    node: MusicRandomSequenceContainer,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    add_transition_matrix(bnk, node, None)

    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=3)


def _create_attributes_music_switch_container(
    bnk: Soundbank,
    node: MusicSwitchContainer,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    from yonder.gui.dialogs.create_state_path_dialog import create_state_path_dialog

    properties.pop("arguments")
    properties.pop("tree_depth")

    args = node.arguments
    names = {a: lookup_name(a, f"#{a}") for a in node.arguments}

    def on_state_path_created(
        sender: str, state_path: list[int], path_node_id: int
    ) -> None:
        node.add_branch(state_path, path_node_id)
        # Regenerate
        on_node_selected(tag, node, user_data)

    def open_context_menu(sender: str, app_data: Any, info: tuple[str, Any]) -> None:
        item, user_data = info
        # TODO allow to edit state values and leaf nodes

    def register_context_menu(tag: str, user_data: Any) -> None:
        registry = f"{tag}_handlers"

        if not dpg.does_item_exist(registry):
            dpg.add_item_handler_registry(tag=registry)

        dpg.add_item_clicked_handler(
            dpg.mvMouseButton_Right,
            callback=open_context_menu,
            user_data=(tag, user_data),
            parent=registry,
        )
        dpg.bind_item_handler_registry(tag, registry)

    def get_key(tree_node: dict) -> str:
        val = tree_node["key"]
        if val == 0:
            return "*"
        return lookup_name(val, f"#{val}")

    def delve(tree_node: dict, level: int) -> None:
        if level == len(args) - 1:
            # Leaf
            nid = tree_node["node_id"]
            leaf_node = bnk.get(nid)

            arg = args[level]
            arg_name = names[arg]
            val_name = get_key(tree_node)

            with dpg.tree_node(label=f"{arg_name} = {val_name}"):
                # TODO should be an input field
                if leaf_node:
                    add_node_link(leaf_node, on_node_selected, user_data=user_data)
                elif nid == 0:
                    dpg.add_text("<None>")
                else:
                    dpg.add_text(f"(ext) {nid}")
        else:
            # Branch
            arg = args[level]
            arg_name = names[arg]
            val_name = get_key(tree_node)

            # TODO add context menu
            with dpg.tree_node(label=f"{arg_name} = {val_name}"):
                for child in tree_node["children"]:
                    delve(child, level + 1)

    with dpg.tree_node(label="Decision Tree", default_open=True):
        for child in node.decision_tree["children"]:
            delve(child, 0)

    dpg.add_spacer(height=3)
    dpg.add_button(
        label="Add State Path",
        callback=lambda: create_state_path_dialog(
            bnk, node, on_state_path_created, raw=True
        ),
    )

    dpg.add_spacer(height=3)
    add_transition_matrix(bnk, node, None)

    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=3)


def _create_attributes_music_track(
    bnk: Soundbank,
    node: MusicTrack,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    def on_wem_selected(
        sender: str, wem_path: Path, info: tuple[int, MusicTrack]
    ) -> None:
        # TODO check if inside soundbank, offer to copy
        # TODO if prefetch streaming create snippet
        index, track = info
        source_details = track.sources[index]["media_information"]
        source_details["source_id"] = int(wem_path.stem)
        source_details["in_memory_media_size"] = wem_path.stat().st_size
        dpg.set_value(sender, wem_path.stem)
        on_node_changed(tag, track, user_data)

    def on_loop_changed(
        sender: str,
        loop_info: tuple[float, float, bool],
        user_data: tuple[int, MusicTrack],
    ) -> None:
        loop_start, loop_end, loop_enabled = loop_info
        source_index, track = user_data
        # TODO update track loop markers

    for i, source in enumerate(node.sources):
        add_generic_widget(
            Path,
            f"source_id #{i}",
            on_wem_selected,
            default=str(source["media_information"]["source_id"]),
            filetypes={"WEMs (.wem)": "*.wem"},
            readonly=True,
            user_data=(i, node),
        )

        add_wav_player(
            lambda idx=i: get_sound_path(bnk, node.sources[idx]),
            loop_markers_enabled=True,
            on_loop_changed=on_loop_changed,
            user_data=(i, node),
        )

    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=3)


def _create_attributes_sound(
    bnk: Soundbank,
    node: Sound,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    properties.pop("media_size")
    properties.pop("source_id")

    def on_wem_selected(sender: str, wem_path: Path, sound: Sound) -> None:
        # TODO check if inside soundbank, offer to copy
        # TODO if prefetch streaming create snippet
        sound.source_id = int(wem_path.stem)
        sound.media_size = wem_path.stat().st_size
        dpg.set_value(sender, wem_path.stem)
        on_node_changed(tag, sound, user_data)

    add_generic_widget(
        Path,
        "source_id",
        on_wem_selected,
        default=str(node.source_id),
        filetypes={"WEMs (.wem)": "*.wem"},
        readonly=True,
        user_data=node,
    )
    add_wav_player(lambda: get_sound_path(bnk, node.source_info))

    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=3)


def _create_attributes_switch_container(
    bnk: Soundbank,
    node: SwitchContainer,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    def on_show_empty_switches(sender: str, show: bool, node: SwitchContainer) -> None:
        for switch, nodes in node.switch_mappings.items():
            dpg.configure_item(
                f"{tag}_node_{node.id}_switch_{switch}",
                show=show or bool(nodes),
            )

    dpg.add_checkbox(
        label="Show empty switches",
        callback=on_show_empty_switches,
        default_value=False,
        user_data=node,
    )

    with dpg.tree_node(label="Switches"):
        for switch, nodes in node.switch_mappings.items():
            label = f"{len(nodes)} - {lookup_name(switch, '?')} ({switch})"
            with dpg.tree_node(
                label=label,
                show=bool(nodes),
                tag=f"{tag}_node_{node.id}_switch_{switch}",
            ):
                for nid in nodes:
                    switch_node = bnk.get(nid)
                    if switch_node:
                        add_node_link(
                            switch_node, on_node_selected, user_data=user_data
                        )
                    else:
                        dpg.add_text(f"(ext) {nid}")

    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=3)
