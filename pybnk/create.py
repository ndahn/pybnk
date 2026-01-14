from typing import Any
import os
from importlib import resources
import json
from pathlib import Path
from logging import getLogger
from enum import IntEnum
import shutil

from pybnk import Soundbank, Node
from pybnk.common.util import calc_hash


class SoundMode(IntEnum):
    REGULAR = 0
    STREAMING = 1
    PREFETCH = 2


class PlaylistMode(IntEnum):
    RANDOM = 0


def new_from_template(
    nid: int, template: str, attributes: dict[str, Any] = None
) -> Node:
    import pybnk

    if not template.endswith(".json"):
        template += ".json"

    template_txt = resources.read_text(pybnk, template)
    template_dict = json.loads(template_txt)
    node = Node(template_dict)
    node.id = nid

    if attributes:
        for path, value in attributes.items():
            node[path] = value

    return node


def new_sound(nid: int, wem: Path, mode: SoundMode = SoundMode.REGULAR) -> Node:
    wem_id = int(wem.name.rsplit(".")[0])
    size = os.path.getsize(str(wem))

    # TODO correct streaming mode name, see what else is needed
    if mode == SoundMode.REGULAR:
        source_type = "BnkData"
    elif mode == SoundMode.STREAMING:
        source_type = "Streaming"
    elif mode == SoundMode.PREFETCH:
        source_type = "Prefetch"

    return new_from_template(
        nid,
        "Sound",
        {
            "bank_source_data/media_information/source_id": wem_id,
            "bank_source_data/media_information/in_memory_media_size": size,
            "bank_source_data/source_type": source_type,
        },
    )


def new_random_sequence_container(
    nid: int,
    children: list[Node | tuple[Node, int]] = None,
    mode: PlaylistMode = PlaylistMode.RANDOM,
    volume: float = -3.0,
) -> Node:
    items = []
    weights = []

    if children:
        for child in children:
            if isinstance(child, tuple):
                child, weight = child
            else:
                weight = 50000

            items.append(child)
            weights.append(weight)

            child.parent = nid

    if mode == PlaylistMode.RANDOM:
        playlist_mode = "Random"

    rsc = new_from_template(
        nid,
        "RandomSequenceContainer",
        {
            "children/items": items,
            "playlist/items": [
                {
                    "play_id": cid,
                    "weight": weight,
                }
                for cid, weight in zip(items, weights)
            ],
            "mode": playlist_mode,
        },
    )

    if volume is not None:
        set_rsc_volume(rsc, volume)

    return rsc


def new_event(
    nid: int, name: str, node: Node | int, action_type: str = "Play"
) -> tuple[Node, Node]:
    if isinstance(node, Node):
        node = node.id

    action = new_from_template(
        "Action", {"action_type": action_type, "initial_values/external_id": node}
    )
    action.id = nid

    event = new_from_template("Event", {"actions": [action.id]})
    event.id = calc_hash(name)

    return (event, action)


def create_simple_sound(
    bnk: Soundbank,
    wwise_name: str,
    wems: list[Path],
    actor_mixer: Node,
    volume: float = -3.0,
) -> Node:
    sounds = []
    for wem in wems:
        try:
            int(wem.stem)
        except ValueError:
            while True:
                wem_id = bnk.new_id()
                new_path = wem.parent / f"{wem_id}.wem"
                if not new_path.is_file():
                    shutil.copy(wem, new_path)
                    print(f"Copied WEM {wem.name} to {new_path.name}")
                    wem = new_path
                    break

        sounds.append(new_sound(bnk.new_id(), wem))

    rsc = new_random_sequence_container(bnk.new_id(), sounds, volume=volume)
    rsc.parent = actor_mixer.id

    play_event, play_action = new_event(
        bnk.new_id(), f"Play_{wwise_name}", rsc.id, action_type="Play"
    )
    stop_event, stop_action = new_event(
        bnk.new_id(), f"Stop_{wwise_name}", rsc.id, action_type="Stop"
    )

    bnk.add_nodes(sounds + [rsc])
    bnk.add_event(play_event, [play_action])
    bnk.add_event(stop_event, [stop_action])


def add_child_to_rsc(bnk: Soundbank, rsc: Node | int, child: Node, weight: int = 50000):
    if isinstance(rsc, int):
        rsc = bnk[rsc]

    if rsc.type != "RandomSequenceContainer":
        raise ValueError("Not a valid RandomSequenceContainer")

    if child.id < 0:
        child.id = bnk.new_id()

    children = rsc["children/items"]

    if child.id in children:
        getLogger.warning(f"Node {child.id} already part of RandomSequenceContainer")
        return

    if child.parent >= 0:
        # TODO we could probably fix this
        getLogger.error(f"Node {child.id} already has a parent")
        return

    children.append(child.id)
    child.parent = rsc.id
    bnk.add_nodes([child])

    rsc["playlist/items"].append(
        {
            "play_id": child.id,
            "weight": weight,
        }
    )


def set_rsc_property(rsc: Node, property: str, value: float):
    path = (
        "initial_values/node_base_params/node_initial_params/prop_initial_values/values"
    )
    properties = rsc[path]

    for prop in properties:
        pt = prop["prop_type"]
        if pt == property:
            prop["value"] = value
            break
    else:
        prop = {
            "prop_type": property,
            "value": value,
        }
        properties.append(prop)


def set_rsc_range_property(
    rsc: Node, property: str, min_value: float, max_value: float
):
    path = "initial_values/node_base_params/node_initial_params/prop_range_modifiers/values"
    properties = rsc[path]

    for prop in properties:
        pt = prop["prop_type"]
        if pt == property:
            prop["min"] = min_value
            prop["max"] = max_value
            break
    else:
        prop = {
            "prop_type": property,
            "min": min_value,
            "max": max_value,
        }
        properties.append(prop)


def set_rsc_volume(
    rsc: Node, volume: float, volume_type: str = "Volume", clean: bool = True
) -> None:
    if clean:
        path = "initial_values/node_base_params/node_initial_params/prop_initial_values/values"
        rsc[path] = [p for p in rsc[path] if "volume" not in p["prop_type"].lower()]

    set_rsc_property(rsc, volume_type, volume)
