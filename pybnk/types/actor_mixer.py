from pybnk.node import Node
from .wwise_node import WwiseNode


class ActorMixer(WwiseNode):
    """A hierarchical container that groups sounds and other mixers. 
    
    Used to organize audio assets and apply shared processing/routing through the mixer hierarchy.
    """

    @classmethod
    def new(cls, nid: int, parent_id: int = 0, 
            override_bus_id: int | Node = 0) -> "ActorMixer":
        """Create a new ActorMixer node.
        
        Parameters
        ----------
        nid : int
            Node ID (hash).
        parent_id : int, default=0
            Parent node ID.
        override_bus_id : int, default=0
            Override bus ID (0 = use parent bus).
            
        Returns
        -------
        ActorMixer
            New ActorMixer instance.
        """
        node = cls.from_template(nid, "ActorMixer")

        if not isinstance(override_bus_id, Node):
            override_bus_id = override_bus_id.id

        mixer = cls(node.dict)
        mixer.override_bus_id = override_bus_id
        if parent_id != 0:
            mixer.parent = parent_id
        
        return mixer

    @property
    def override_bus_id(self) -> int:
        """Get or set the override bus ID.

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
