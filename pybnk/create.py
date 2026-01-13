import os
from importlib import resources
import json
from pathlib import Path
from logging import getLogger
from enum import IntEnum

from pybnk import Soundbank, Node


class SoundMode(IntEnum):
    REGULAR = 0
    STREAMING = 1
    PREFETCH = 2


class PlaylistMode(IntEnum):
    RANDOM = 0


def new_from_template(template: str, **kwargs) -> Node:
    import pybnk

    if not template.endswith(".json"):
        template += ".json"

    template_txt = resources.read_text(pybnk, template)
    template_dict = json.loads(template_txt)
    node = Node(template_dict)

    for path, value in kwargs.items():
        node[path] = value

    return node


def create_sound(wem: Path, mode: SoundMode) -> Node:
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
        "Sound",
        {
            "bank_source_data/media_information/source_id": wem_id,
            "bank_source_data/media_information/in_memory_media_size": size,
            "bank_source_data/source_type": source_type,
        },
    )


def new_random_sequence_container(
    children: list[(dict | int) | tuple[dict | int, int]] = None,
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

    if mode == PlaylistMode.RANDOM:
        playlist_mode = "Random"

    return new_from_template(
        "RandomSequenceContainer",
        {
            "children/items": items,
            "playlist/items": [
                {
                    "play_id": id,
                    "weight": weight,
                }
                for id, weight in zip(items, weights)
            ],
            "mode": playlist_mode,
            "initial_values/node_base_params/node_initial_params/prop_initial_values/values": [
                {
                    "prop_type": "Volume",
                    "value": volume,
                }
            ],
        },
    )


def add_child_to_rsc(bnk: Soundbank, rsc: Node | int, child: Node, weight: int = 50000):
    if isinstance(rsc, int):
        rsc = bnk[rsc]

    if rsc.type != "RandomSequenceContainer":
        raise ValueError("Not a valid RandomSequenceContainer")

    if child.id < 0:
        child.id = bnk.new_id()

    child_id = child.id
    children = rsc["children/items"]

    if child_id in children:
        getLogger.warning(f"Node {child_id} already part of RandomSequenceContainer")
        return

    if child.parent >= 0:
        # TODO we could probably fix this
        getLogger.error(f"Node {child_id} already has a parent")
        return

    children.append(child_id)
    child.parent = rsc.id
    bnk.add_node(child)

    rsc["playlist/items"].append(
        {
            "play_id": child_id,
            "weight": weight,
        }
    )


def set_rsc_volume(
    rsc: Node, volume: float, volume_type: str = "Volume", clean: bool = True
) -> None:
    path = (
        "initial_values/node_base_params/node_initial_params/prop_initial_values/values"
    )
    properties = []
    volume_prop = None

    for prop in rsc[path]:
        pt = prop["prop_type"]

        if pt == volume_type:
            volume_prop = prop

        # Remove all other volume settings like GameAuxSendVolume
        elif clean and "volume" in pt.lower():
            continue

        properties.append(prop)

    if not volume_prop:
        volume_prop = {
            "prop_type": volume_type,
            "value": volume,
        }
        properties.append(volume_prop)

    rsc[path] = properties
