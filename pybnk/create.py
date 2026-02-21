from typing import Any, Literal
import os
from importlib import resources
import json
from pathlib import Path
from enum import IntEnum

from pybnk import Soundbank, Node
from pybnk.modify import set_rsc_volume, add_children
from pybnk.util import calc_hash, get_event_name
from pybnk.enums import SoundType


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


def create_empty_soundbank(path: Path | str, name: str) -> "Soundbank":
    import pybnk

    if not path.is_dir():
        raise ValueError(f"{path} is not a directory")

    bnk = json.loads(resources.read_text(pybnk, "resources/empty_soundbank.json"))
    name_hash = calc_hash(name)
    bnk["sections"][0]["body"]["BKHD"]["bank_id"] = name_hash

    bnk_path = Path(path) / name / "soundbank.json"
    json.dump(bnk, bnk_path.open("w"))

    return Soundbank.load(bnk_path)


def new_sound(
    bnk: Soundbank,
    wem: Path,
    mode: Literal["Embedded", "PrefetchStreaming"] = "Embedded",
    attr: dict[str, Any] = None,
) -> Node:
    wem_id = int(wem.name.rsplit(".")[0])
    size = os.path.getsize(str(wem))

    # TODO source duration (in ms)
    # https://docs.google.com/document/d/1Dx8U9q6iEofPtKtZ0JI1kOedJYs9ifhlO7H5Knil5sg/edit?tab=t.0
    # https://discord.com/channels/529802828278005773/1252503668515934249

    return new_from_template(
        bnk.new_id(),
        "Sound",
        {
            "bank_source_data/source_type": mode,
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
    action_type: Literal["Play", "Stop"],
    action_attr: dict[str, Any] = None,
) -> tuple[Node, Node]:
    if isinstance(node, Node):
        node = node.id

    action = new_from_template(
        bnk.new_id(),
        f"Action_{action_type}",
        {"external_id": node} | (action_attr or {}),
    )

    # Only set for play actions?
    if action_type == "Play":
        action[f"params/{action_type}/bank_id"] = bnk.id

    event = new_from_template(
        bnk.new_id(), "Event", {"actions": [action.id]}
    )
    event.id = calc_hash(name)

    return (event, action)


def create_simple_sound(
    bnk: Soundbank,
    sound_type: SoundType,
    wwise_id: int,
    wems: list[Path] | Path,
    actor_mixer: Node,
    volume: float = -3.0,
    rsc_attr: dict[str, Any] = None,
) -> Node:
    wwise_name = get_event_name(sound_type, wwise_id)

    if isinstance(wems, Path):
        wems = [wems]

    sounds = [new_sound(bnk, w) for w in wems]
    rsc = new_random_sequence_container(bnk, sounds, volume=volume, attr=rsc_attr)
    rsc.parent = actor_mixer.id

    play_event, play_action = new_event(
        bnk, f"Play_{wwise_name}", rsc.id, "Play"
    )
    stop_event, stop_action = new_event(
        bnk, f"Stop_{wwise_name}", rsc.id, "Stop"
    )

    bnk.add_nodes(sounds + [rsc])
    bnk.add_event(play_event, [play_action])
    bnk.add_event(stop_event, [stop_action])
