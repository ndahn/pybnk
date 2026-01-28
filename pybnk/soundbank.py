from typing import Any, Generator
from pathlib import Path
from random import randrange
from collections import deque
import json
import copy
import shutil
import networkx as nx

from pybnk.util import calc_hash, logger
from pybnk.node import Node


class Soundbank:
    @classmethod
    def load(cls, bnk_path: Path | str) -> "Soundbank":
        """Load a soundbank and return a more manageable representation."""
        # Resolve the path to the unpacked soundbank
        bnk_path: Path = Path(bnk_path).absolute().resolve()
        if bnk_path.name == "soundbank.json":
            json_path = bnk_path
            bnk_path = bnk_path.parent
        else:
            json_path = bnk_path / "soundbank.json"
            bnk_path = bnk_path
        
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

        return cls(bnk_path, bnk_json, bnk_id, hirc)

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

        # A helper dict for mapping object IDs to HIRC indices
        self._id2index: dict[int, int] = {}
        self._regenerate_index_table()

    def _regenerate_index_table(self):
        self._id2index.clear()

        for idx, node in enumerate(self.hirc):
            idsec = node.dict["id"]
            if "Hash" in idsec:
                oid = idsec["Hash"]
                self._id2index[oid] = idx
            elif "String" in idsec:
                eid = idsec["String"]
                self._id2index[eid] = idx
                # Events are sometimes referred to by their hash, but it's not included in the json
                oid = calc_hash(eid)
                self._id2index[oid] = idx
            else:
                logger.error(f"Don't know how to handle object with id {idsec}")

    @property
    def name(self) -> str:
        return self.bnk_dir.name

    def wems(self) -> list[int]:
        wems = []
        for sound in self.query({"type": "Sound"}):
            wid = sound["bank_source_data/media_information/source_id"]
            wems.append(wid)

        return wems

    def update_json(self) -> None:
        """Update this soundbank's json with its current HIRC."""
        sections = self.json["sections"]
        for sec in sections:
            if "HIRC" in sec["body"]:
                sec["body"]["HIRC"]["objects"] = [n.dict for n in self.hirc]
                break

    def copy(self, name: str, new_bnk_id: int = None) -> "Soundbank":
        self.update_json()
        
        bnk = Soundbank(
            self.bnk_dir.parent / name,
            copy.deepcopy(self.json),
            self.id,
            [n.copy() for n in self.hirc],
        )

        if new_bnk_id is not None:
            bnk.id = new_bnk_id
            for action in bnk.query({"type": "Action"}):
                bid = action.get("params/bank_id", None)
                if bid == self.id:
                    action["params/bank_id"] = new_bnk_id

        return bnk

    def save(self, path: Path = None, backup: bool = True) -> None:
        self.update_json()

        if not path:
            path = self.bnk_dir

        if path.name != "soundbank.json":
            if not path.is_dir():
                raise ValueError(f"Not a directory: {path}")
            path = path / "soundbank.json"

        if backup and path.is_file():
            shutil.copy(path, str(path) + ".bak")

        with path.open("w") as f:
            json.dump(self.json, f, indent=2)

    def new_id(self) -> int:
        while True:
            id = randrange(10000000, 100000000)
            if id not in self._id2index:
                return id

    def get_insertion_index(self, nodes: list[Node]) -> tuple[int, int]:
        min_idx = 0
        max_idx = len(self.hirc)

        for node in nodes:
            try:
                parent = node.parent
                max_idx = min(max_idx, self._id2index[parent])
            except KeyError:
                pass

            if "children" in node:
                children: list = node["children/items"]
                for child in children:
                    min_idx = max(min_idx, self._id2index[child])

        if min_idx > max_idx:
            raise ValueError(f"Invalid index constraints: {min_idx} >= {max_idx}")

        return min_idx

    def add_nodes(self, nodes: list[Node]) -> int:
        idx = self.get_insertion_index(nodes)

        # NOTE not resolving the correct order of nodes, up to the caller for now
        for i, node in enumerate(nodes):
            if node.id in self._id2index:
                raise ValueError(
                    f"A node with ID {node.id} is already in the soundbank"
                )

            if node.id <= 0:
                raise ValueError(f"Invalid ID {node.id}")

            if node.parent <= 0:
                raise ValueError(f"Invalid parent ID {node.parent}")

            logger.info(f"Inserting new node {node} at {idx + i}")
            self.hirc.insert(idx + i, node)

        self._regenerate_index_table()
        return idx

    def add_event(self, event: Node, actions: list[Node]) -> int:
        # Events appear towards the end of the soundbank
        first_event = self.query_one({"type": "Event"})
        idx = self._id2index[first_event.id]

        # TODO set event actions

        logger.info(f"Inserting new event {event} with {len(actions)} actions at {idx}")
        self.hirc.insert(idx, event)
        for act in reversed(actions):
            self.hirc.insert(idx, act)

        self._regenerate_index_table()
        return idx

    def get_hierarchy(self, entrypoint: Node) -> nx.DiGraph:
        """Collects all descendant nodes from the specified entrypoint in a graph."""
        g = nx.DiGraph()
        todo = deque([(entrypoint.id, None)])

        # Depth first search to recover all nodes part of the wwise hierarchy
        while todo:
            node_id, parent_id = todo.pop()

            if node_id in g:
                continue

            idx = self._id2index[node_id]
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

    def get_parent_chain(self, entrypoint: Node) -> list[int]:
        """Go up in the HIRC from the specified entrypoint and collect all node IDs along the way until we reach the top."""
        parent_id = entrypoint.parent
        upchain = []

        # Parents are sometimes located in other soundbanks, too
        while parent_id != 0 and parent_id in self._id2index:
            # No early exit, we want to recover the entire upwards chain. We'll handle the
            # parts we actually need later

            # Check for loops. No clue if that ever happens, but better be safe than sorry
            if parent_id in upchain:
                # Print the loop
                logger.error(f"Reference loop detected: {upchain}")
                for pid in upchain:
                    debug_obj: Node = self[pid]
                    debug_parent = debug_obj.parent
                    print(f"{pid} -> {debug_parent}")

                print(f"{debug_parent} -> {parent_id}")

                raise ValueError(
                    f"Parent chain for node {entrypoint} contains a loop at node {parent_id}"
                )

            # Children before parents
            upchain.append(parent_id)
            parent_id = self[parent_id].parent

        return upchain

    def query(self, conditions: dict[str, Any]) -> Generator[Node, None, None]:
        for node in self.hirc:
            for path, val in conditions.items():
                if path == "type":
                    if node.type != val:
                        break
                elif path in ("id", "hash"):
                    if node.id != val:
                        break
                elif node[path] != val:
                    break
            else:
                # Node matched all conditions
                yield node

    def query_one(self, conditions: dict[str, Any], default: Any = None) -> Node:
        return next(self.query(conditions), default)

    def find_events(self, event_type: str = "Play") -> Generator[Node, None, None]:
        events = list(self.query({"type": "Event"}))
        for evt in events:
            for aid in evt["actions"]:
                action = self[aid]
                if event_type in action.get("params", {}):
                    yield evt
                    break

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
                if item in self._id2index and item not in object_ids:
                    new_ids.add(item)

        for oid in object_ids:
            todo = deque([oid])

            while todo:
                node_id = todo.pop()
                node = self.hirc[self._id2index[node_id]]

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
                        issues.append(
                            f"{node_id}:reference to external soundbank {item}"
                        )

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
                    issues.append(
                        f"{node_id}: {path}: reference {item} does not exist (probably okay?)"
                    )

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
            issues.append(
                f"Expected nodes not found: {[required_ids.difference(verified_ids)]}"
            )

        return issues

    def __contains__(self, key: Any) -> Node:
        if isinstance(key, Node):
            key = key.id
        elif isinstance(key, str):
            key = calc_hash(key)

        return key in self._id2index

    def __getitem__(self, key: int | str) -> Node:
        if isinstance(key, str):
            key = calc_hash(key)

        idx = self._id2index[key]
        return self.hirc[idx]

    def __str__(self):
        return f"Soundbank (id={self.id}, bnk={self.name})"
