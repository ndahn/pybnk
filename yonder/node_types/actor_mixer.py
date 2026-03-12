from yonder.node import Node
from yonder.util import logger
from .wwise_node import WwiseNode
from .mixins import ContainerMixin


class ActorMixer(WwiseNode, ContainerMixin):
    """A hierarchical container that groups sounds and other mixers.

    Used to organize audio assets and apply shared processing/routing through the mixer hierarchy.
    """

    @classmethod
    def new(
        cls,
        nid: int,
        override_bus_id: int | Node = 0,
        parent: int | Node = None,
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

        logger.info(f"Created new node {mixer}")
        return mixer

    @property
    def override_bus_id(self) -> int:
        """Override bus ID.

        Returns
        -------
        int
            Bus ID (0 = use parent bus).
        """
        return self.base_params["override_bus_id"]

    @override_bus_id.setter
    def override_bus_id(self, value: int | Node) -> None:
        if isinstance(value, Node):
            value = value.id

        self.base_params["override_bus_id"] = value
