from typing import Any, Iterator


_undefined = object()


class Node:
    def __init__(self, node_dict: dict):
        self._attr = node_dict
        self._type = next(iter(self._attr["body"].keys()))

    @property
    def dict(self) -> dict:
        return self._attr

    @property
    def id(self) -> int:
        """Get the ID of a HIRC node (i.e. its hash)."""
        return next(iter(self._attr["id"].values()))

    @id.setter
    def id(self, id: int) -> None:
        self._attr["id"] = id

    @property
    def parent(self) -> int:
        """Get the ID of a node's parent node."""
        return self["node_base_params/direct_parent_id"]

    @parent.setter
    def parent(self, parent: int) -> None:
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
        def delve(item: dict | list | Any, path: str):
            if path:
                yield path

            if isinstance(item, list):
                for idx, value in enumerate(item):
                    delve(value, path + f":{idx}")

            elif isinstance(item, dict):
                for key, value in item.items():
                    delve(value, path + "/" + key)
        
        delve(self.body, "")

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
            raise KeyError(f"Path {path} not found in template {self}") from e

    def __str__(self):
        return f"{self.type} ({self.id})"
