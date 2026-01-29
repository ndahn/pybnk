from typing import Any
import os
from importlib import resources
import json
import logging
from pathlib import Path
from enum import IntEnum
import shutil

from pybnk import Soundbank, Node
from pybnk.modify import set_rsc_volume, add_children
from pybnk.util import calc_hash


class SoundMode(IntEnum):
    EMBEDDED = 0
    STREAMING = 1
    PREFETCH = 2


class PlaylistMode(IntEnum):
    RANDOM = 0


def new_from_template(
    nid: int, template: str, attr: dict[str, Any] = None
) -> Node:
    import pybnk

    if not template.endswith(".json"):
        template += ".json"

    template_txt = resources.read_text(pybnk, "resources/templates/" + template)
    template_dict = json.loads(template_txt)
    node = Node(template_dict)
    node.id = nid

    if attr:
        for path, value in attr.items():
            node[path] = value

    return node


def new_sound(
    bnk: Soundbank,
    wem: Path,
    mode: SoundMode = SoundMode.EMBEDDED,
    attr: dict[str, Any] = None,
) -> Node:
    wem_id = int(wem.name.rsplit(".")[0])
    size = os.path.getsize(str(wem))

    # TODO correct streaming mode name, see what else is needed
    if mode == SoundMode.EMBEDDED:
        source_type = "Embedded"
    elif mode == SoundMode.STREAMING:
        source_type = "Streaming"
    elif mode == SoundMode.PREFETCH:
        source_type = "Prefetch"

    # TODO source duration (in ms)
    # https://docs.google.com/document/d/1Dx8U9q6iEofPtKtZ0JI1kOedJYs9ifhlO7H5Knil5sg/edit?tab=t.0
    # https://discord.com/channels/529802828278005773/1252503668515934249

    return new_from_template(
        bnk.new_id(),
        "Sound",
        {
            "bank_source_data/source_type": source_type,
            "bank_source_data/media_information/source_id": wem_id,
            "bank_source_data/media_information/in_memory_media_size": size,
        }
        | (attr or {}),
    )


def new_random_sequence_container(
    bnk: Soundbank,
    children: list[Node | tuple[Node, int]] = None,
    mode: PlaylistMode = PlaylistMode.RANDOM,
    volume: float = -3.0,
    attr: dict[str, Any] = None,
) -> Node:
    items = []
    weights = []

    rsc_id = bnk.new_id()

    if children:
        for child in children:
            if isinstance(child, tuple):
                child, weight = child
            else:
                weight = 50000

            items.append(child)
            weights.append(weight)

            child.parent = rsc_id

    if mode == PlaylistMode.RANDOM:
        playlist_mode = "Random"

    rsc = new_from_template(
        rsc_id,
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
        }
        | (attr or {}),
    )

    if volume is not None:
        set_rsc_volume(rsc, volume)

    return rsc


def new_actor_mixer(
    bnk: Soundbank, children: list[Node], attr: dict[str, Any] = None
) -> Node:
    am = new_from_template(bnk.new_id(), "ActorMixer", attr)
    add_children(am, *children)
    return am


def new_event(
    bnk: Soundbank,
    name: str,
    node: Node | int,
    play_attr: dict[str, Any] = None,
    stop_attr: dict[str, Any] = None,
) -> tuple[Node, tuple[Node, Node]]:
    if isinstance(node, Node):
        node = node.id

    play_action = new_from_template(
        bnk.new_id(),
        "Action_Play",
        {"external_id": node, "params/Play/bank_id": bnk.id} | (play_attr or {}),
    )
    stop_action = new_from_template(
        bnk.new_id(),
        "Action_Stop",
        {"external_id": node} | (stop_attr or {}),
    )

    event = new_from_template(
        bnk.new_id(), "Event", {"actions": [play_action.id, stop_action.id]}
    )
    event.id = calc_hash(name)

    return (event, (play_action, stop_action))


def create_simple_sound(
    bnk: Soundbank,
    wwise_name: str,
    wems: list[Path],
    actor_mixer: Node,
    volume: float = -3.0,
    rsc_attr: dict[str, Any] = None,
) -> Node:
    sounds = [new_sound(bnk, w) for w in wems]
    rsc = new_random_sequence_container(bnk, sounds, volume=volume, attr=rsc_attr)
    rsc.parent = actor_mixer.id

    play_event, play_action = new_event(
        bnk, f"Play_{wwise_name}", rsc.id, action_type="Play"
    )
    stop_event, stop_action = new_event(
        bnk, f"Stop_{wwise_name}", rsc.id, action_type="Stop"
    )

    bnk.add_nodes(sounds + [rsc])
    bnk.add_event(play_event, [play_action])
    bnk.add_event(stop_event, [stop_action])
