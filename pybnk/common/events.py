from typing import TYPE_CHECKING, Generator
import re

from .util import calc_hash
from .attributes import get_body, get_node_type

if TYPE_CHECKING:
    from ..soundbank import Soundbank


def get_events(bnk: "Soundbank") -> Generator[tuple[int, dict], None, None]:
    for i, obj in enumerate(bnk.hirc):
        if get_node_type(obj) == "Event":
            yield (i, obj)


def get_event_name(sound_type: str, event_id: int, event_type: str = "Play") -> str:
    if sound_type not in "acfopsmvxbiyzegd":
        print(f"Warning: unexpected sound type {sound_type}")

    if not 0 < event_id < 1_000_000_000:
        print(f"Warning: event ID {event_id} outside expected range")

    if not event_type:
        raise ValueError("No event type given")

    return f"{event_type}_{sound_type}{event_id:010d}"


def get_event_idx(bnk: "Soundbank", event: str) -> int:
    if not re.match(r"\w+_\w\d{9}", event):
        print(f"Warning: event {event} does not match the expected pattern")

    idx = bnk.id2index.get(event, None)
        
    if idx is not None:
        return idx
    
    play_evt_hash = calc_hash(event)
    idx = bnk.id2index.get(play_evt_hash)
    
    if idx is not None:
        return idx
    
    raise ValueError(f"Could not find index for event {event}")


def get_event_actions(bnk: "Soundbank", event: str) -> list[int]:
    actions = []

    idx = get_event_idx(bnk, event)
    event_obj = bnk.hirc[idx]
    event_actions = get_body(event_obj)["actions"]
    
    for action_hash in event_actions:
        action = bnk.hirc[bnk.id2index[action_hash]]
        target_id = get_body(action)["external_id"]
        if target_id in bnk.id2index:
            actions.append(target_id)
        else:
            print(f"Warning: action {action_hash} of event {event} has external ID outside the current soundbank")

    return actions
