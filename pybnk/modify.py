import logging

from pybnk import Soundbank, Node


def add_children(node: Node, *children: Node) -> None:
    items = node["children"]

    for child in children:
        if child.id in items:
            continue

        items.append(child.id)
        child.parent = node.id

    items.sort()


def add_child_to_rsc(bnk: Soundbank, rsc: Node | int, child: Node, weight: int = 50000):
    if isinstance(rsc, int):
        rsc = bnk[rsc]

    if rsc.type != "RandomSequenceContainer":
        raise ValueError("Not a valid RandomSequenceContainer")

    if child.id < 0:
        child.id = bnk.new_id()

    children = rsc["children/items"]

    if child.id in children:
        logging.warning(f"Node {child.id} already part of RandomSequenceContainer")
        return

    if child.parent >= 0:
        # TODO we could probably fix this
        logging.warning(f"Node {child.id} already has a parent")
        return

    add_children(rsc, child)

    child.parent = rsc.id
    if child not in bnk:
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
