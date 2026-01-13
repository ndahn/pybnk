from typing import Any


def set_attribute(node: dict, path: str, value: Any) -> None:
    body = get_body(node)

    try:
        parts = path.split("/")
        attr = body

        for sub in parts[:-1]:
            attr = attr[sub]
        
        attr[parts[-1]] = value
    except KeyError as e:
        raise KeyError(f"Path {path} not found in template {node}") from e


def set_id(node: dict, id: int) -> None:
    node["id"] = id


def set_parent(node: dict, parent: int) -> None:
    set_attribute(node, "node_base_params/direct_parent_id", parent)


def get_id(node: dict) -> int:
    """Get the ID of a HIRC node (i.e. its hash)."""
    return next(iter(node["id"].values()))


def get_node_type(node: dict) -> str:
    """Get the type of a HIRC node (e.g. RandomSequenceContainer)."""
    return next(iter(node["body"].keys()))


def get_body(node: dict) -> dict:
    """Return the body of a node where the relevant attributes are stored."""
    return node["body"][get_node_type(node)]


def get_parent_id(node: dict) -> int:
    """Get the ID of a node's parent node."""
    body = get_body(node)
    return body["node_base_params"]["direct_parent_id"]

