from typing import Any, Iterator
from importlib import resources
import json
import copy

from pybnk.util import calc_hash, lookup_table, logger


_undefined = object()


class Node:
    @classmethod
    def from_template(
        cls,
        nid: int, template: str, attr: dict[str, Any] = None
    ) -> "Node":
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

    def __init__(self, node_dict: dict):
        self._attr = node_dict
        self._type = next(iter(self._attr["body"].keys()))

    @property
    def dict(self) -> dict:
        return self._attr

    def copy(self, new_id: int = None, parent: int = None) -> "Node":
        attr = copy.deepcopy(self._attr)
        n = Node(attr)

        if new_id is not None:
            n.id = new_id
        if parent is not None:
            n.parent = parent

        return n

    def lookup_name(self, default: str = None) -> str:
        idsec = self._attr["id"]
        s = idsec.get("String")
        if not s:
            s = lookup_table.get(self.id)
            if s:
                idsec["String"] = s
        
        if s is None:
            return default
            
        return s

    @property
    def id(self) -> int:
        """Get the ID of a HIRC node (i.e. its hash)."""
        idsec = self._attr["id"]
        h = idsec.get("Hash")
        if not h:
            h = calc_hash(idsec["String"])
            idsec["Hash"] = h
        
        return h

    @id.setter
    def id(self, id: int | str) -> None:
        idsec = self._attr["id"]
        if isinstance(id, int):
            idsec["Hash"] = id
            idsec.pop("String", None)
        elif isinstance(id, str):
            idsec["Hash"] = calc_hash(id)
            idsec["String"] = id
        else:
            raise ValueError(f"Invalid node ID {id}")

    @property
    def parent(self) -> int:
        """Get the ID of a node's parent node."""
        # NOTE: some nodes like buses don't have a direct_parent_id
        return self.get("node_base_params/direct_parent_id", None)

    @parent.setter
    def parent(self, parent: "Node | int") -> None:
        if isinstance(parent, Node):
            parent = parent.id

        if not isinstance(parent, int):
            raise ValueError(f"Invalid parent {parent}")
        
        if self.parent > 0 and parent > 0 and parent != self.parent:
            logger.warning(f"Node {self} is being assigned new parent {parent}")
        
        self["node_base_params/direct_parent_id"] = parent

    @property
    def type(self) -> str:
        """Get the type of a HIRC node (e.g. RandomSequenceContainer)."""
        return self._type

    @property
    def body(self) -> dict:
        """Return the body of a node where the relevant attributes are stored."""
        return self._attr["body"][self.type]

    def paths(self) -> Iterator[str]:
        def delve(item: dict, path: str):
            if path:
                yield path

            # if isinstance(item, list):
            #     for idx, value in enumerate(item):
            #         delve(value, path + f":{idx}")

            if isinstance(item, dict):
                for key, value in item.items():
                    delve(value, path + "/" + key)
        
        yield from delve(self.body, "")

    def get(self, path: str, default: Any = _undefined) -> Any:
        try:
            return self[path]
        except KeyError as e:
            if default != _undefined:
                return default
            
            raise e

    def set(self, path: str, value: Any) -> bool:
        try:
            self[path] = value
            return True
        except KeyError:
            return False

    def __hash__(self):
        return self.id

    def __contains__(self, path: Any) -> bool:
        if not isinstance(path, str):
            return False

        for p in self.paths():
            if p == path:
                return True

        return False

    def __getitem__(self, path: str) -> Any:
        if not path:
            raise ValueError("Empty path")

        val = self.body
        for sub in path.split("/"):
            val = val[sub]

        return val

    def __setitem__(self, path: str, val: Any) -> None:
        try:
            parts = path.split("/")
            attr = self.body

            for sub in parts[:-1]:
                attr = attr[sub]
            
            attr[parts[-1]] = val
        except KeyError as e:
            raise KeyError(f"Path '{path}' not found in node {self}") from e

    def __str__(self):
        return f"{self.type} ({self.id})"
