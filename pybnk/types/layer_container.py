from .wwise_node import WwiseNode


class LayerContainer(WwiseNode):
    """Plays multiple child sounds simultaneously as layers. 
    
    Useful for layered sound design where different components play together (e.g., engine loop + transmission sounds).
    """

    @property
    def layer_count(self) -> int:
        """Get the number of layers.

        Returns
        -------
        int
            Number of layers in the container.
        """
        return self["layer_count"]

    @property
    def layers(self) -> list[dict]:
        """Get the list of layers.

        Returns
        -------
        list[dict]
            List of layer definitions.
        """
        return self["layers"]

    @property
    def is_continuous_validation(self) -> bool:
        """Get or set continuous validation flag.

        Returns
        -------
        bool
            True if continuous validation is enabled.
        """
        return bool(self["is_continuous_validation"])

    @is_continuous_validation.setter
    def is_continuous_validation(self, value: bool) -> None:
        self["is_continuous_validation"] = int(value)

    @property
    def children_ids(self) -> list[int]:
        """Get list of child node IDs.

        Returns
        -------
        list[int]
            List of child node hash IDs.
        """
        return self["children/items"]

    def add_child(self, child_id: int | WwiseNode) -> None:
        """Add a child node to the container.

        Parameters
        ----------
        child_id : int | WwiseNode
            Child node ID or Node instance.
        """
        if isinstance(child_id, WwiseNode):
            child_id = child_id.id

        children = self["children/items"]
        if child_id not in children:
            children.append(child_id)
            self["children/count"] = len(children)

    def remove_child(self, child_id: int | WwiseNode) -> bool:
        """Remove a child node from the container.

        Parameters
        ----------
        child_id : int | WwiseNode
            Child node ID or Node instance to remove.

        Returns
        -------
        bool
            True if child was removed, False if not found.
        """
        if isinstance(child_id, WwiseNode):
            child_id = child_id.id

        children = self["children/items"]
        if child_id in children:
            children.remove(child_id)
            self["children/count"] = len(children)
            return True
        return False

    def clear_children(self) -> None:
        """Remove all children from the container."""
        self["children/items"] = []
        self["children/count"] = 0

    # Seems to not be used in ER/NR, so no clue what would go here
    def add_layer(self, layer: dict) -> None:
        """Add a layer definition to the container.

        Parameters
        ----------
        layer : dict
            Layer definition dictionary.
        """
        self["layers"].append(layer)
        self["layer_count"] = len(self["layers"])

    def clear_layers(self) -> None:
        """Remove all layers from the container."""
        self["layers"] = []
        self["layer_count"] = 0
