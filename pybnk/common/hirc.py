from typing import TYPE_CHECKING, Any
from random import randrange
from collections import deque
import networkx as nx

from .attributes import get_body, get_node_type, get_id, get_parent_id

if TYPE_CHECKING:
    from pybnk.soundbank import Soundbank


def new_id(bnk: "Soundbank") -> int:
    while True:
        id = randrange(10000000, 100000000)
        if id not in bnk.id2index:
            return id


def get_hierarchy(bnk: "Soundbank", entrypoint_id: int) -> nx.DiGraph:
    """Collects all descendant nodes from the specified entrypoint in a graph."""
    g = nx.DiGraph()
    todo = deque([(entrypoint_id, None)])

    # Depth first search to recover all nodes part of the wwise hierarchy
    while todo:
        node_id, parent_id = todo.pop()

        if node_id in g:
            continue

        idx = bnk.id2index[node_id]
        node = bnk.hirc[idx]
        node_type = get_node_type(node)
        node_params = get_body(node)

        g.add_node(node_id, index=idx, type=node_type, body=node_params)

        if parent_id is not None:
            g.add_edge(parent_id, node_id)

        if node_type == "Sound":
            # We found an actual sound
            wem = node_params["bank_source_data"]["media_information"]["source_id"]
            g.nodes[node_id]["wem"] = wem

        if "children" in node_params:
            children = node_params["children"].get("items", [])

            for cid in children:
                todo.append((cid, node_id))

    return g


def get_parent_chain(bnk: "Soundbank", entrypoint_id: int) -> deque:
    """Go up in the HIRC from the specified entrypoint and collect all node IDs along the way until we reach the top."""
    entrypoint = bnk.hirc[bnk.id2index[entrypoint_id]]
    parent_id = get_parent_id(entrypoint)

    upchain = deque()

    # Parents are sometimes located in other soundbanks, too
    while parent_id != 0 and parent_id in bnk.id2index:
        # No early exit, we want to recover the entire upwards chain. We'll handle the 
        # parts we actually need later

        # Check for loops. No clue if that ever happens, but better be safe than sorry
        if parent_id in upchain:
            # Print the loop
            for idx in upchain:
                debug_obj = bnk.hirc[idx]
                debug_obj_id = get_id(debug_obj)
                debug_parent = get_parent_id(debug_obj)
                print(f"{debug_obj_id} -> {debug_parent}")
            
            print(f"{debug_parent} -> {parent_id}")

            raise ValueError(f"Parent chain for node {entrypoint_id} contains a loop at node {parent_id}")
            
        # Children before parents
        upchain.append(parent_id)
        parent = bnk.hirc[bnk.id2index[parent_id]]
        parent_id = get_parent_id(parent)

    return upchain


def collect_extras(bnk: "Soundbank", object_ids: list[int]) -> set[int]:
    """Collect any values of attributes that look like they could be a reference to another object, e.g. a bus."""
    extras = []

    # TODO instead of just taking everything that even remotely looks like an object we really should decide based on node type and attribute name, but.... eh
    def delve(item: Any, field: str, new_ids: set):
        if field in ["source_id", "direct_parent_id", "children"]:
            return
        
        if isinstance(item, list):
            for i, subnode in enumerate(item):
                delve(subnode, f"{field}[{i}]", new_ids)

        elif isinstance(item, dict):
            for key, val in item.items():
                delve(val, key, new_ids)

        elif isinstance(item, int):
            if item in bnk.id2index and item not in object_ids:
                new_ids.add(item)

    for oid in object_ids:
        todo = deque([oid])

        while todo:
            node_id = todo.pop()
            node = bnk.hirc[bnk.id2index[node_id]]
            body = get_body(node)

            new_ids = set()
            delve(body, "body", new_ids)

            for id in new_ids.difference(extras):
                todo.append(id)
                # Will contain the highest parents in the beginning (to the left) and deeper 
                # children towards the end (right)
                extras.append(id)

    return extras
