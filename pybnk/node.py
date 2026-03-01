from typing import Any, Iterator, Generator
from importlib import resources
import json
import copy
from collections import deque

from pybnk.hash import calc_hash, lookup_table
from pybnk.util import logger
from pybnk.enums import reference_fields


_undefined = object()


class Node:
    @classmethod
    def load_template(cls, template: str) -> dict:
        import pybnk

        if not template.endswith(".json"):
            template += ".json"

        path = "resources/templates/" + template
        template_txt = resources.files(pybnk).joinpath(path).read_text()
        return json.loads(template_txt)

    @classmethod
    def wrap(cls, node_dict: dict, *args, **kwargs):
        # Make sure the subclasses have been loaded
        import pybnk.types

        def all_subclasses(c: type) -> list[type[Node]]:
            return set(c.__subclasses__()).union(
                [s for c in c.__subclasses__() for s in all_subclasses(c)]
            )

        tp = next(iter(node_dict["body"].keys()))
        for sub in all_subclasses(cls):
            if sub.__name__ == tp:
                return sub(node_dict, *args, **kwargs)

        return cls(node_dict, *args, **kwargs)

    def __init__(self, node_dict: dict):
        self._attr = node_dict
        self._type = next(iter(self._attr["body"].keys()))

    def cast(self) -> "Node":
        return Node.wrap(self._attr)

    def json(self) -> str:
        return json.dumps(self._attr, indent=2)

    def update(self, data: dict, delete_missing: bool = False) -> None:
        # Merge with our attr so that references stay valid and the soundbank's
        # HIRC this node belongs to is updated, too
        def merge(target, source):
            if isinstance(target, dict) and isinstance(source, dict):
                # Remove keys that don't exist in source
                if delete_missing:
                    keys_to_remove = set(target.keys()) - set(source.keys())
                    for key in keys_to_remove:
                        del target[key]

                # Update or add keys from source
                for key, value in source.items():
                    if (
                        key in target
                        and isinstance(target[key], (dict, list))
                        and isinstance(value, (dict, list))
                    ):
                        # Recursively update if both are containers
                        merge(target[key], value)
                    else:
                        # Replace with new value
                        target[key] = value

            elif isinstance(target, list) and isinstance(source, list):
                # Clear list and extend with new values
                target.clear()
                target.extend(source)
            else:
                # Type changed, replace old value
                target[key] = source[key]

            return target

        merge(self._attr, data)

    @property
    def dict(self) -> dict:
        return self._attr

    @property
    def type(self) -> str:
        """Type of a HIRC node (e.g. RandomSequenceContainer)."""
        return self._type

    @property
    def id(self) -> int:
        """ID of a HIRC node (i.e. its hash)."""
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
        """ID of a node's parent node."""
        # TODO: some nodes like buses don't have a direct_parent_id
        # TODO some nodes like MusicRandomSequenceContainer have their base params at a deeper level
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
    def body(self) -> dict:
        """Return the body of a node where the relevant attributes are stored."""
        return self._attr["body"][self.type]

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

    def set(self, path: str, value: Any, create: bool = False) -> bool:
        try:
            self[path] = value
            return True
        except KeyError:
            if create:
                obj: dict = self.body
                parts = path.split("/")
                for p in parts[:-1]:
                    obj = obj.setdefault(p, {})
                    if not isinstance(obj, dict):
                        raise ValueError(f"Tried to set new path, but {p} already exists")

                obj[-1] = value
                return True

            return False

    def resolve_path(self, path: str) -> tuple[str, Any] | list[tuple[str, Any]]:
        if not path:
            raise ValueError("Empty path")

        parts = path.split("/")

        def bfs_search(
            data: dict, target_key: str
        ) -> Generator[tuple[list[str], dict], None, None]:
            queue = deque([(data, [])])

            while queue:
                current, current_path = queue.popleft()

                if isinstance(current, dict):
                    if target_key in current:
                        yield current_path, current

                    for key, value in current.items():
                        queue.append((value, current_path + [key]))

                elif isinstance(current, list):
                    for i, item in enumerate(current):
                        queue.append((item, current_path + [str(i)]))

        def delve(
            obj: Any, key_index: int, resolved: list[str]
        ) -> tuple[str, Any] | list[tuple[str, Any]]:
            if key_index >= len(parts):
                return ("/".join(resolved), obj)

            key = parts[key_index]

            if key == "*":
                if not isinstance(obj, dict):
                    raise KeyError(
                        f"{path} resulted in '*' being applied on non-dict item"
                    )

                results = [
                    delve(sub, key_index + 1, resolved + [k])
                    for k, sub in obj.items()
                    if sub
                ]

                if len(results) == 1:
                    return results[0]

                return results

            elif key == "**":
                if key_index >= len(parts):
                    raise KeyError(f"'**' can not appear at the end ({path})")

                if not isinstance(obj, dict):
                    raise KeyError(
                        f"{path} resulted in '**' being applied on non-dict item"
                    )

                next_key = parts[key_index + 1]
                results = [
                    delve(sub, key_index + 1, resolved + bfs_path)
                    for bfs_path, sub in bfs_search(obj, next_key)
                    if sub
                ]

                if len(results) == 1:
                    return results[0]

                return results

            elif ":" in key:
                key, idx = key.split(":")
                obj = obj[key]

                if not isinstance(obj, list):
                    raise KeyError(
                        f"{path} resulted in array access on a non-list item"
                    )

                if idx == "*":
                    return [
                        delve(item, key_index + 1, resolved + [f"{key}:{i}"])
                        for i, item in enumerate(obj)
                    ]
                else:
                    idx = int(idx)
                    return delve(obj[idx], key_index + 1, resolved + [f"{key}:{idx}"])

            else:
                return delve(obj[key], key_index + 1, resolved + [key])

        return delve(self.body, 0, [])

    def get_references(self, include_unset: bool = False) -> list[tuple[str, int]]:
        refs = []
        for node_type, paths in reference_fields.items():
            if node_type in ("*", self.type):
                for path in paths:
                    result = self.resolve_path(path)
                    if isinstance(result, tuple):
                        result = [result]

                    for p, ref in result:
                        if include_unset or (isinstance(ref, int) and ref > 0):
                            refs.append((p, ref))

        return refs

    def __contains__(self, item: Any) -> bool:
        if not isinstance(item, str):
            return False

        return self.get(item, None) is not None

    def __getitem__(self, path: str) -> Any | list[Any]:
        if not path:
            raise ValueError("Empty path")

        parts = path.split("/")
        value = self.body

        for key in parts:
            value = value[key]

        return value

    def __setitem__(self, path: str, val: Any) -> None:
        try:
            parts = path.split("/")
            attr = self.body

            for sub in parts[:-1]:
                attr = attr[sub]

            attr[parts[-1]] = val
        except KeyError as e:
            raise KeyError(f"Path '{path}' not found in node {self}") from e

    def __hash__(self):
        return self.id

    def __str__(self):
        return f"{self.type} ({self.id})"
