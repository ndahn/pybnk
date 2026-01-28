from typing import TYPE_CHECKING
import re

from pybnk.util import calc_hash, logger

if TYPE_CHECKING:
    from pybnk.soundbank import Soundbank



def get_event_name(sound_type: str, event_id: int, event_type: str = "Play") -> str:
    if sound_type not in "acfopsmvxbiyzegd":
        logger.warning(f"unexpected sound type {sound_type}")

    if not 0 < event_id < 1_000_000_000:
        logger.warning(f"event ID {event_id} outside expected range")

    if not event_type:
        raise ValueError("No event type given")

    return f"{event_type}_{sound_type}{event_id:010d}"


def get_event_idx(bnk: "Soundbank", event: str) -> int:
    if not re.match(r"\w+_\w\d{9}", event):
        logger.warning(f"event {event} does not match the expected pattern")

    idx = bnk._id2index.get(event, None)
        
    if idx is not None:
        return idx
    
    play_evt_hash = calc_hash(event)
    idx = bnk._id2index.get(play_evt_hash)
    
    if idx is not None:
        return idx
    
    raise ValueError(f"Could not find index for event {event}")


def get_event_actions(bnk: "Soundbank", event: str) -> list[int]:
    actions = []

    idx = get_event_idx(bnk, event)
    event_node = bnk.hirc[idx]
    event_actions = event_node["actions"]
    
    for action_hash in event_actions:
        action = bnk.hirc[bnk._id2index[action_hash]]
        target_id = action["external_id"]
        if target_id in bnk._id2index:
            actions.append(target_id)
        else:
            logger.warning(f"action {action_hash} of event {event} has external ID outside the current soundbank")

    return actions
