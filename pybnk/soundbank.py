from typing import Any, Generator
from pathlib import Path
from random import randrange
from collections import deque
import logging
import json
import networkx as nx

from pybnk.common.util import calc_hash
from pybnk.node import Node


class Soundbank:
    @classmethod
    def load(cls, bnk_dir: str) -> "Soundbank":
        """Load a soundbank and return a more manageable representation."""
        # Resolve the path to the unpacked soundbank
        bnk_dir: Path = Path(bnk_dir)
        if not bnk_dir.is_absolute():
            bnk_dir = Path(__file__).resolve().parent / bnk_dir
        
        bnk_dir = bnk_dir.resolve()

        json_path = bnk_dir / "soundbank.json"
        with json_path.open() as f:
            bnk_json: dict = json.load(f)

        # Read the sections
        sections = bnk_json.get("sections", None)

        if not sections:
            raise ValueError("Could not find 'sections' in bnk")

        for sec in sections:
            body = sec["body"]

            if "BKHD" in body:
                bnk_id = body["BKHD"]["bank_id"]
            elif "HIRC" in body:
                hirc: list[Node] = [Node(obj) for obj in body["HIRC"]["objects"]]
            else:
                pass

        return Soundbank(bnk_dir, bnk_json, bnk_id, hirc)

    def __init__(
        self,
        bnk_dir: Path,
        json: dict,
        id: int,
        hirc: list[Node],
    ):
        self.bnk_dir = bnk_dir
        self.json = json
        self.id = id
        self.hirc = hirc

        self.logger = logging.getLogger()
        
        # A helper dict for mapping object IDs to HIRC indices
        self.id2index: dict[int, int] = {}
        self._regenerate_id_lookup()

    def _regenerate_id_lookup(self):
        for idx, node in enumerate(self.hirc):
            idsec = node.dict["id"]
            if "Hash" in idsec:
                oid = idsec["Hash"]
                self.id2index[oid] = idx
            elif "String" in idsec:
                eid = idsec["String"]
                self.id2index[eid] = idx
                # Events are sometimes referred to by their hash, but it's not included in the json
                oid = calc_hash(eid)
                self.id2index[oid] = idx
            else:
                print(f"Don't know how to handle object with id {idsec}")

    def update_json(self) -> None:
        """Update this soundbank's json with its current HIRC."""
        sections = self.json["sections"]
        for sec in sections:
            if "HIRC" in sec["body"]:
                sec["body"]["HIRC"]["objects"] = [n.dict for n in self.hirc]
                break

    def __getitem__(self, key: int) -> Node:
        idx = self.id2index[key]
        return self.hirc[idx]

    def new_id(self) -> int:
        while True:
            id = randrange(10000000, 100000000)
            if id not in self.id2index:
                return id

    def add_node(self, node: Node) -> int:
        if node.id in self.id2index:
            raise ValueError(f"A node with ID {node.id} is already in the soundbank")

        if node.id <= 0:
            raise ValueError(f"Invalid ID {node.id}")

        if node.parent <= 0:
            raise ValueError(f"Invalid parent ID {node.parent}")

        # Find out where to insert the node
        related = self.find_related_objects([node.id])
        parent_id = node.parent
        min_idx = 0
        max_idx = self.id2index[parent_id]

        for oid in related:
            # Must be defined before its parent
            if oid == parent_id:
                continue

            oid_idx = self.id2index.get(oid)
            if oid_idx is not None:
                min_idx = max(oid_idx + 1, min_idx)

        if min_idx >= max_idx:
            raise ValueError(f"Invalid index constraints: {min_idx} >= {max_idx}")

        self.logger.info(f"Inserting new node {node} at {min_idx}")
        self.hirc.insert(min_idx, node)
        self._regenerate_id_lookup()

    def get_events(self) -> Generator[tuple[int, Node], None, None]:
        for i, node in enumerate(self.hirc):
            if node.type == "Event":
                yield (i, node)

    def get_hierarchy(self, entrypoint: Node) -> nx.DiGraph:
        """Collects all descendant nodes from the specified entrypoint in a graph."""
        g = nx.DiGraph()
        todo = deque([(entrypoint.id, None)])

        # Depth first search to recover all nodes part of the wwise hierarchy
        while todo:
            node_id, parent_id = todo.pop()

            if node_id in g:
                continue

            idx = self.id2index[node_id]
            node = self.hirc[idx]
            node_type = node.type
            node_params = node.body

            g.add_node(node_id, index=idx, type=node_type, body=node_params)

            if parent_id is not None:
                g.add_edge(parent_id, node_id)

            if node_type == "Sound":
                # We found an actual sound
                wem = node["bank_source_data/media_information/source_id"]
                g.nodes[node_id]["wem"] = wem

            if "children" in node_params:
                children = node_params["children"].get("items", [])

                for cid in children:
                    todo.append((cid, node_id))

        return g

    def get_parent_chain(self, entrypoint: Node) -> deque:
        """Go up in the HIRC from the specified entrypoint and collect all node IDs along the way until we reach the top."""
        parent_id = entrypoint.parent

        upchain = deque()

        # Parents are sometimes located in other soundbanks, too
        while parent_id != 0 and parent_id in self.id2index:
            # No early exit, we want to recover the entire upwards chain. We'll handle the 
            # parts we actually need later

            # Check for loops. No clue if that ever happens, but better be safe than sorry
            if parent_id in upchain:
                # Print the loop
                for idx in upchain:
                    debug_obj: Node = self.hirc[idx]
                    debug_obj_id = debug_obj.id
                    debug_parent = debug_obj.parent
                    print(f"{debug_obj_id} -> {debug_parent}")
                
                print(f"{debug_parent} -> {parent_id}")

                raise ValueError(f"Parent chain for node {entrypoint} contains a loop at node {parent_id}")
                
            # Children before parents
            upchain.append(parent_id)
            parent = self.hirc[self.id2index[parent_id]]
            parent_id = parent.id

        return upchain

    def find_related_objects(self, object_ids: list[int]) -> set[int]:
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
                if item in self.id2index and item not in object_ids:
                    new_ids.add(item)

        for oid in object_ids:
            todo = deque([oid])

            while todo:
                node_id = todo.pop()
                node = self.hirc[self.id2index[node_id]]

                new_ids = set()
                delve(node.body, "body", new_ids)

                for id in new_ids.difference(extras):
                    todo.append(id)
                    # Will contain the highest parents in the beginning (to the left) and deeper 
                    # children towards the end (right)
                    extras.append(id)

        return extras

    def verify(self, required_ids: list[int] = None) -> list[str]:
        discovered_ids = set([0])
        issues = []

        required_ids: set = set(required_ids or [])
        verified_ids = set()

        # We check absolutely everything!
        def delve(item: dict | list | Any, node_id: int, path: str):
            if isinstance(item, list):
                for idx, value in enumerate(item):
                    delve(value, node_id, path + f"[{idx}]")

            elif isinstance(item, dict):
                for key, value in item.items():
                    delve(value, node_id, path + "/" + key)

            # There's like one 5-digit hash (possibly empty string?), all others are above 10 mio
            elif isinstance(item, int) and item >= 1000000:
                if path.endswith("source_id"):
                    # WEMs won't appear in the HIRC
                    pass

                elif path.endswith("bank_id"):
                    if item != self.id:
                        # Not sure if this can be an issue
                        issues.append(f"{node_id}:reference to external soundbank {item}")
                
                elif path.endswith("id/Hash"):
                    if item in discovered_ids:
                        issues.append(f"{node_id}: has duplicates")

                elif path.endswith("id/String"):
                    if calc_hash(item) in discovered_ids:
                        issues.append(f"{node_id}: has duplicates")
                
                elif path.endswith("direct_parent_id"):
                    if item in discovered_ids:
                        issues.append(f"{node_id}: is defined after its parent {item}")

                elif item not in discovered_ids:
                    issues.append(f"{node_id}: {path}: reference {item} does not exist (probably okay?)")

        for node in self.hirc:
            node_id = node.id

            if node_id in discovered_ids:
                issues.append(f"{node_id}: node has been defined before")
                continue

            discovered_ids.add(node_id)
            if node_id not in required_ids:
                continue

            delve(node.body, node_id, "")

            # References to other objects will always be by hash
            if isinstance(node_id, str):
                node_id = calc_hash(node_id)

            verified_ids.add(node_id)

        if required_ids and len(verified_ids) < len(required_ids):
            issues.append(f"Expected nodes not found: {[required_ids.difference(verified_ids)]}")

        return issues
