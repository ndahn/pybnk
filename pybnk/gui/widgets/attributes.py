from typing import Any, Callable
from collections import deque
from pathlib import Path
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk import Soundbank, Node
from pybnk.hash import get_name_for_hash
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
from pybnk.gui import style
from .paragraphs import add_paragraphs
from .generic_input_widget import add_generic_widget
from .properties_table import add_properties_table
from .player_widget import add_wav_player


def create_attribute_widgets(
    bnk: Soundbank,
    node: Node,
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
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
    # TODO
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
        pass
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
    node: SwitchContainer,
    properties: dict[str, property],
    on_node_changed: Callable[[str, Node, Any], None],
    on_node_selected: Callable[[str, Node, Any], None],
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> None:
    properties.pop("arguments", None)
    args = [f"{get_name_for_hash(a, '?')} ({a})" for a in node.arguments]
    dpg.add_listbox(args, label="arguments")  # TODO


def _create_attributes_sound(
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
    def on_wem_selected(sender: str, wem_path: Path, sound: Sound) -> None:
        sound.source_id = int(wem_path.stem)
        sound.media_size = wem_path.stat().st_size
        dpg.set_value(sender, wem_path.stem)
        on_node_changed(
            tag,
        )

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

    add_wav_player(lambda: node.get_source_path(bnk))

    dpg.add_spacer(height=5)


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
            label = f"{len(nodes)} - {get_name_for_hash(switch, '?')} ({switch})"
            with dpg.tree_node(
                label=label,
                show=bool(nodes),
                tag=f"{tag}_node_{node.id}_switch_{switch}",
            ):
                for nid in nodes:
                    switch_node = bnk.get(nid)
                    if switch_node:
                        dpg.add_button(
                            label=str(switch_node),
                            small=True,
                            callback=lambda s, a, u: on_node_selected(
                                tag, u, user_data
                            ),
                            user_data=node,
                        )
                        dpg.bind_item_theme(dpg.last_item(), style.themes.link_button)
                    else:
                        dpg.add_text(f"(ext) {nid}")

    dpg.add_spacer(height=5)
