from yonder.node import Node, NodeLike
from yonder.enums import VirtualQueueBehavior
from yonder.util import logger, PathDict
from .mixins import RtpcMixin, StateChunkMixin, PropertiesMixin


class WwiseNode(RtpcMixin, StateChunkMixin, PropertiesMixin, Node):
    """Base class for nodes with common node_base_params functionality.

    Provides convenient access to shared parameters like aux sends, virtual voice behavior, and state management.
    """
    base_params_path = "node_base_params"


    @property
    def base_params(self) -> PathDict:
        return PathDict(self[self.base_params_path])

    @property
    def parent(self) -> int:
        """ID of a node's parent node."""
        return self.base_params["direct_parent_id"]

    @parent.setter
    def parent(self, value: int | Node) -> None:
        if isinstance(value, Node):
            value = value.id

        if not isinstance(value, int):
            raise ValueError(f"Invalid parent {value}")

        old_parent = self.parent
        if old_parent > 0 and value > 0 and value != old_parent:
            logger.warning(f"Node {self} is being assigned new parent {value}")

        self.base_params["direct_parent_id"] = value

    @property
    def max_instances(self) -> int:
        """Maximum number of concurrent instances.

        Returns
        -------
        int
            Maximum instance count (0 = unlimited).
        """
        return self.base_params["adv_settings_params/max_instance_count"]

    @max_instances.setter
    def max_instances(self, value: int) -> None:
        self.base_params["adv_settings_params/max_instance_count"] = value

    @property
    def virtual_queue_behavior(self) -> VirtualQueueBehavior:
        """Virtual voice queue behavior.

        Returns
        -------
        str
            Behavior mode (e.g., 'Resume', 'PlayFromElapsedTime', 'PlayFromBeginning').
        """
        return self.base_params["adv_settings_params/virtual_queue_behavior"]

    @virtual_queue_behavior.setter
    def virtual_queue_behavior(self, value: VirtualQueueBehavior) -> None:
        self.base_params["adv_settings_params/virtual_queue_behavior"] = value

    @property
    def use_virtual_behavior(self) -> bool:
        """Whether virtual voice behavior is enabled.

        Returns
        -------
        bool
            True if virtual voices are used.
        """
        return self.base_params["adv_settings_params/use_virtual_behavior"]

    @use_virtual_behavior.setter
    def use_virtual_behavior(self, value: bool) -> None:
        self.base_params["adv_settings_params/use_virtual_behavior"] = value

    @property
    def override_bus(self) -> NodeLike:
        return self.base_params["override_bus_id"]

    @override_bus.setter
    def override_bus(self, bus_id: NodeLike) -> None:
        self.base_params["override_bus_id"] = bus_id

    def get_aux_bus(self, index: int) -> int:
        """Get an auxiliary bus ID by index.

        Parameters
        ----------
        index : int
            Aux bus index (1-4).

        Returns
        -------
        int
            Aux bus ID.
        """
        if index < 1 or index > 4:
            raise ValueError("Aux index must be between 1 and 4")
        return self.base_params["aux_params/aux{index}"]

    def set_aux_bus(self, index: int, bus_id: int) -> None:
        """Set an auxiliary bus ID by index.

        Parameters
        ----------
        index : int
            Aux bus index (1-4).
        bus_id : int
            Aux bus ID to set.
        """
        if index < 1 or index > 4:
            raise ValueError("Aux index must be between 1 and 4")
        self.base_params["aux_params/aux{index}"] = bus_id

    def get_references(self) -> list[int]:
        refs = super().get_references()

        paths = (
            f"{self.base_params_path}/override_bus_id",
            f"{self.base_params_path}/aux_params/aux1",
            f"{self.base_params_path}/aux_params/aux2",
            f"{self.base_params_path}/aux_params/aux3",
            f"{self.base_params_path}/aux_params/aux4",
        )
        refs.extend([(p, r) for p in paths if (r := self.get(p, 0)) > 0])

        return refs
