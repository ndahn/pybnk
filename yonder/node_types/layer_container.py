from yonder.node import Node
from yonder.util import logger
from .wwise_node import WwiseNode
from .mixins import ContainerMixin


class LayerContainer(WwiseNode, ContainerMixin):
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

        logger.info(f"Created new node {container}")
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
