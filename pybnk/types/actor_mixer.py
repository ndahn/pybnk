from pybnk.node import Node
from pybnk.util import logger
from .wwise_node import WwiseNode


class ActorMixer(WwiseNode):
    """A hierarchical container that groups sounds and other mixers.

    Used to organize audio assets and apply shared processing/routing through the mixer hierarchy.
    """

    @classmethod
    def new(
        cls, nid: int, override_bus_id: int | Node = 0, parent: int | Node = None, 
    ) -> "ActorMixer":
        """Create a new ActorMixer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        override_bus_id : int, default=0
            Override bus ID (0 = use parent bus).
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        ActorMixer
            New ActorMixer instance.
        """
        temp = cls.load_template(cls.__name__)

        if not isinstance(override_bus_id, Node):
            override_bus_id = override_bus_id.id

        mixer = cls(temp)
        mixer.id = nid
        mixer.override_bus_id = override_bus_id
        if parent is not None:
            mixer.parent = parent

        return mixer

    @property
    def override_bus_id(self) -> int:
        """Override bus ID.

        Returns
        -------
        int
            Bus ID (0 = use parent bus).
        """
        return self["node_base_params/override_bus_id"]

    @override_bus_id.setter
    def override_bus_id(self, value: int | Node) -> None:
        if isinstance(value, Node):
            value = value.id
        self["node_base_params/override_bus_id"] = value

    @property
    def children_ids(self) -> list[int]:
        """Get list of child node IDs.

        Returns
        -------
        list[int]
            List of child node hash IDs.
        """
        return self["children/items"]

    def add_child(self, child_id: int | Node) -> None:
        """Add a child node to the mixer.

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
        """Remove a child node from the mixer.

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
        """Remove all children from the mixer."""
        self["children/items"] = []
        self["children/count"] = 0
