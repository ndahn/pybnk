from typing import Any
import os
from importlib import resources
import json
from pathlib import Path
from logging import getLogger
from enum import IntEnum

from pybnk import Soundbank
from pybnk.common.hirc import get_node_type, get_body, get_id, get_parent_id, new_id
from pybnk.common.attributes import set_attribute, set_parent, set_id


class SoundMode(IntEnum):
    REGULAR = 0
    STREAMING = 1
    PREFETCH = 2


class PlaylistMode(IntEnum):
    RANDOM = 0


def read_template(template: str) -> dict:
    import pybnk

    if not template.endswith(".json"):
        template += ".json"

    return json.loads(resources.read_text(pybnk, template))


def new_from_template(template: str, **kwargs) -> dict:
    tmp = read_template(template)
    for path, value in kwargs.items():
        set_attribute(tmp, path, value)

    return tmp


def create_sound(wem: Path, mode: SoundMode) -> dict:
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
    loop = 1,  # TODO
    volume = -6.0,  # TODO
):
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
        },
    )


def add_child_to_rsc(
    bnk: Soundbank, rsc: dict | int, child: dict, weight: int = 50000
):
    if isinstance(rsc, int):
        rsc = bnk[rsc]

    if get_node_type(rsc) != "RandomSequenceContainer":
        raise ValueError("Not a valid RandomSequenceContainer")

    if get_id(child) < 0:
        set_id(child, new_id(bnk))

    child_id = get_id(child)
    rsc_body = get_body(rsc)
    children = rsc_body["children"]["items"]

    if child_id in children:
        getLogger.warning(f"Node {child_id} already part of RandomSequenceContainer")
        return

    if get_parent_id(child) >= 0:
        # TODO we could probably fix this
        getLogger.error(f"Node {child_id} already has a parent")
        return

    children.append(child_id)
    set_parent(child, get_id(rsc))

    # TODO add child to hirc

    rsc_body["playlist"]["items"].append(
        {
            "play_id": child_id,
            "weight": weight,
        }
    )
