from typing import Any, Literal
from importlib import resources
import json
from pathlib import Path

from pybnk import Soundbank, Node
from pybnk.hash import calc_hash
from pybnk.types import Event, Action, RandomSequenceContainer, Sound
from pybnk.util import logger


def new_from_template(nid: int, template: str, attr: dict[str, Any] = None) -> Node:
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


def new_event(
    bnk: Soundbank,
    name: str,
    node: Node | int,
    action_type: Literal["Play", "Stop"],
    action_attr: dict[str, Any] = None,
) -> tuple[Node, Node]:
    if isinstance(node, Node):
        node = node.id

    # TODO use class methods instead
    action = new_from_template(
        bnk.new_id(),
        f"Action_{action_type}",
        {"external_id": node} | (action_attr or {}),
    )

    # Only set for play actions?
    if action_type == "Play":
        action[f"params/{action_type}/bank_id"] = bnk.id

    event = new_from_template(bnk.new_id(), "Event", {"actions": [action.id]})
    event.id = calc_hash(name)

    return (event, action)


def create_simple_sound(
    bnk: Soundbank,
    event_name: str,
    wems: list[Path] | Path,
    actor_mixer: int | Node,
    avoid_repeats: bool = False,
    properties: dict[str, float] = None,
) -> tuple[tuple[Event, Event], RandomSequenceContainer, list[Sound]]:
    """Create a new sound structure with one or more sounds in a RandomSequenceContainer controlled by a start and stop event.

    Parameters
    ----------
    bnk : Soundbank
        The soundbank to add the structure to.
    event_name : str
        Base name of the new events.
    wems : list[Path] | Path
        Audio files to add.
    actor_mixer : int | Node
        The ActorMixer to attach the new RandomSequenceContainer to.
    avoid_repeats : bool, optional
        If True the container will avoid playing the same sound twice in a row.
    properties : dict[str, float], optional
        Properties to apply to the RandomSequenceContainer.

    Returns
    -------
    Node
        _description_
    """
    if isinstance(wems, Path):
        wems = [wems]

    rsc = RandomSequenceContainer.new(
        bnk.new_id(),
        avoid_repeats=avoid_repeats,
        loop_count=1,
        parent=actor_mixer,
    )
    if properties:
        for key, val in properties.items():
            rsc.set_property(key, val)
    rsc.avoid_repeats = avoid_repeats

    sounds = []
    for w in wems:
        snd = Sound.new_from_wem(bnk.new_id(), w, rsc)
        rsc.add_child(snd)
        sounds.append(snd)

    play = Event.new(f"Play_{event_name}")
    play_action = Action.new_play_action(bnk.new_id(), rsc.id)
    play.add_action(play_action)

    stop = Event.new(f"Stop_{event_name}")
    stop_action = Action.new_stop_action(bnk.new_id(), rsc.id)
    stop.add_action(stop_action)

    bnk.add_nodes(rsc, *sounds, play, play_action, stop, stop_action)

    # Add the RSC to the actor mixer
    if isinstance(actor_mixer, int):
        if actor_mixer == 0:
            logger.warning(
                f"No ActorMixer specified for RSC {rsc.id} of new sound {event_name}"
            )
        else:
            amx_node = bnk.get(actor_mixer)
            if not amx_node:
                logger.warning(
                    f"ActorMixer {actor_mixer} not found in soundbank {bnk}. If it is part of another soundbank, make sure to add the RSC's ID ({rsc.id}) to its children!"
                )
            else:
                amx_node.cast().add_child(rsc)
    elif isinstance(actor_mixer, Node):
        actor_mixer.cast().add_child(rsc)

    return ((play, stop), rsc, sounds)
