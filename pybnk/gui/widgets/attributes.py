from typing import Any, Callable
from collections import deque
from pathlib import Path
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.hash import lookup_name
from pybnk.node_types import (
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
from pybnk.util import logger
from pybnk.gui import style
from .paragraphs import add_paragraphs
from .generic_input_widget import add_generic_widget
from .properties_table import add_properties_table
from .player_widget import add_wav_player


# Somewhat ugly, but it shouldn't be saved in the config nor in the soundbank
_streaming_dir: Path = None


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
        sender: str, properties: dict[str, float], node: WwiseNode
    ) -> None:
        for key, val in properties.items():
            node.set_property(key, val)

    def set_property(sender: str, new_value: Any, prop: property):
        prop.fset(node, new_value)
        on_node_changed(tag, node, user_data)

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

        dpg.add_child_window(height=-30, border=False)
        dpg.add_button(label="Reset")

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
    from pybnk.gui.dialogs.file_dialog import open_file_dialog
    global _streaming_dir

    def locate_wem(wem: str) -> Path:
        for subdir in ("wem", "enus/wem"):
            p = _streaming_dir / subdir / wem[:2] / f"{wem}.wem"
            if p.is_file():
                return p

        return None

    source_id = source["media_information"]["source_id"]

    if source["source_type"] in ("Streaming", "PrefetchStreaming"):
        if not _streaming_dir:
            _streaming_dir = bnk.bnk_dir.parent

        wem_file = locate_wem(str(source_id))

        if not wem_file:
            ret = open_file_dialog(
                title="Find game folder", 
                default_dir=str(bnk.bnk_dir.parent),
                filetypes={"Executable (.exe)": "*.exe"},
            )
            if ret:
                _streaming_dir = Path(ret).parent / "sd"
                wem_file = locate_wem(str(source_id))

        if wem_file:
            logger.info(f"Located wem {source_id} at {wem_file}")

        return wem_file
    
    return bnk.bnk_dir.parent / f"{source_id}.wem"


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
        pass
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
    from pybnk.gui.dialogs.create_state_path_dialog import create_state_path_dialog

    def on_state_path_created(
        sender: str, state_path: list[str], path_node_id: int
    ) -> None:
        node.add_branch(state_path, path_node_id)
        # Regenerate
        on_node_selected(tag, node, user_data)

    properties.pop("arguments", None)
    args = node.arguments
    names = {a: lookup_name(a, f"#{a}") for a in node.arguments}

    def delve(tree_node: dict, level: int) -> None:
        if level == len(args) - 1:
            # Leaf
            nid = tree_node["node_id"]
            leaf_node = bnk.get(nid)

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
            val = tree_node["key"]
            if val == 0:
                val_name = "*"
            else:
                val_name = lookup_name(val, f"#{val}")

            with dpg.tree_node(label=f"{arg_name} = {val_name}"):
                for child in tree_node["children"]:
                    delve(child, level + 1)

    with dpg.tree_node(label="Decision Tree"):
        for child in node.decision_tree["children"]:
            delve(child, 0)

    dpg.add_spacer(height=3)
    dpg.add_button(
        label="Add State Path",
        callback=lambda: create_state_path_dialog(node, on_state_path_created),
    )

    # TODO transition rules

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
        index, track = info
        source_details = track.sources[index]["media_information"]
        source_details["source_id"] = int(wem_path.stem)
        source_details["in_memory_media_size"] = wem_path.stat().st_size
        dpg.set_value(sender, wem_path.stem)
        on_node_changed(tag, track, user_data)

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

        add_wav_player(lambda idx=i: get_sound_path(bnk, node.sources[idx]))

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
    def on_wem_selected(sender: str, wem_path: Path, sound: Sound) -> None:
        # TODO check if inside soundbank, offer to copy
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
    properties.pop("media_size")
    properties.pop("source_id")

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
