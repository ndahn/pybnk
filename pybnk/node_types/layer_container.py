from pybnk.node import Node
from pybnk.util import logger
from .wwise_node import WwiseNode


class LayerContainer(WwiseNode):
    """Plays multiple child sounds simultaneously as layers.

    Useful for layered sound design where different components play together (e.g., engine loop + transmission sounds).
    """

    @classmethod
    def new(cls, nid: int, parent: int | Node = None) -> "LayerContainer":
        """Create a new LayerContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        LayerContainer
            New LayerContainer instance.
        """
        temp = cls.load_template(cls.__name__)

        container = cls(temp)
        container.id = nid
        if parent is not None:
            container.parent = parent

        return container

    @property
    def layers(self) -> list[dict]:
        """Layer definitions for simultaneous playback configuration.

        Returns
        -------
        list[dict]
            List of layer definitions.
        """
        return self["layers"]

    @property
    def continuous_validation(self) -> bool:
        """Controls whether layer validation runs continuously during playback.

        Returns
        -------
        bool
            True if continuous validation is enabled.
        """
        return bool(self["is_continuous_validation"])

    @continuous_validation.setter
    def continuous_validation(self, value: bool) -> None:
        self["is_continuous_validation"] = int(value)

    @property
    def children_ids(self) -> list[int]:
        """Child nodes that play as layers within this container.

        Returns
        -------
        list[int]
            List of child node hash IDs.
        """
        return self["children/items"]

    def add_child(self, child_id: int | Node) -> None:
        """Associates a child node as a layer within this container.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance.
        """
        if isinstance(child_id, Node):
            if child_id.parent > 0 and child_id.parent != self.id:
                logger.warning(f"Adding already adopted child {child_id} to {self}")
            
            child_id = child_id.id

        children = self["children/items"]
        if child_id not in children:
            children.append(child_id)
            self["children/count"] = len(children)

    def remove_child(self, child_id: int | Node) -> bool:
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
        if isinstance(child_id, Node):
            child_id = child_id.id

        children = self["children/items"]
        if child_id in children:
            children.remove(child_id)
            self["children/count"] = len(children)
            return True
        return False

    def clear_children(self) -> None:
        """Disassociates all children from this container."""
        self["children/items"] = []
        self["children/count"] = 0

    # NOTE Seems to not be used in ER/NR, so no clue what would go here
    def add_layer(self, layer: dict) -> None:
        """Associates a layer definition with this container.

        Parameters
        ----------
        layer : dict
            Layer definition dictionary.
        """
        self["layers"].append(layer)
        self["layer_count"] = len(self["layers"])

    def clear_layers(self) -> None:
        """Disassociates all layer definitions from this container."""
        self["layers"] = []
        self["layer_count"] = 0