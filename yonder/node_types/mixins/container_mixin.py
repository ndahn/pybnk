from typing import TYPE_CHECKING

from yonder.util import logger

if TYPE_CHECKING:
    from yonder.node import Node


class ContainerMixin:
    children_path: str = "children"


    @property
    def children(self) -> list[int]:
        """Get list of child segment IDs.

        Returns
        -------
        list[int]
            List of child segment hash IDs.
        """
        return self[f"{self.children_path}/items"]

    def add_child(self, child_id: "int | Node") -> None:
        """Associates a child node for random or sequential playback.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance.
        """
        from yonder.node import Node
        
        if isinstance(child_id, Node):
            if child_id.parent > 0 and child_id.parent != self.id:
                logger.warning(f"Adding already adopted child {child_id} to {self}")

            child_id = child_id.id

        children: list[int] = self[f"{self.children_path}/items"]
        if child_id not in children:
            children.append(child_id)
            self[f"{self.children_path}/count"] = len(children)
            children.sort()

    def remove_child(self, child_id: "int | Node") -> bool:
        """Disassociates a child node from this container.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance to remove.

        Returns
        -------
        bool
            True if child was removed, False if not found.
        """
        if isinstance(child_id, "Node"):
            child_id = child_id.id

        children = self[f"{self.children_path}/items"]
        if child_id in children:
            children.remove(child_id)
            self[f"{self.children_path}/count"] = len(children)
            return True

        return False

    def clear_children(self) -> None:
        """Disassociates all children from this container."""
        self[f"{self.children_path}/items"] = []
        self[f"{self.children_path}/count"] = 0

    def get_references(self) -> list[tuple[str, int]]:
        refs = super().get_references()

        for i, child_id in enumerate(self.children):
            refs.append((f"{self.children_path}/items:{i}", child_id))

        return refs
