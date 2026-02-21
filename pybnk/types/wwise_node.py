from typing import Any

from pybnk.node import Node


class WwiseNode(Node):
    """Base class for nodes with common node_base_params functionality.

    Provides convenient access to shared parameters like aux sends,
    virtual voice behavior, and state management.
    """

    @property
    def max_instances(self) -> int:
        """Get or set the maximum number of concurrent instances.

        Returns
        -------
        int
            Maximum instance count (0 = unlimited).
        """
        return self["node_base_params/adv_settings_params/max_instance_count"]

    @max_instances.setter
    def max_instances(self, value: int) -> None:
        self["node_base_params/adv_settings_params/max_instance_count"] = value

    @property
    def use_virtual_behavior(self) -> bool:
        """Get or set whether virtual voice behavior is enabled.

        Returns
        -------
        bool
            True if virtual voices are used.
        """
        return self["node_base_params/adv_settings_params/use_virtual_behavior"]

    @use_virtual_behavior.setter
    def use_virtual_behavior(self, value: bool) -> None:
        self["node_base_params/adv_settings_params/use_virtual_behavior"] = value

    @property
    def virtual_queue_behavior(self) -> str:
        """Get or set the virtual voice queue behavior.

        Returns
        -------
        str
            Behavior mode (e.g., 'Resume', 'PlayFromElapsedTime', 'PlayFromBeginning').
        """
        return self["node_base_params/adv_settings_params/virtual_queue_behavior"]

    @virtual_queue_behavior.setter
    def virtual_queue_behavior(self, value: str) -> None:
        self["node_base_params/adv_settings_params/virtual_queue_behavior"] = value

    @property
    def has_aux(self) -> bool:
        """Get or set whether auxiliary sends are enabled.

        Returns
        -------
        bool
            True if aux sends are active.
        """
        return self["node_base_params/aux_params/has_aux"]

    @has_aux.setter
    def has_aux(self, value: bool) -> None:
        self["node_base_params/aux_params/has_aux"] = value

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
        return self[f"node_base_params/aux_params/aux{index}"]

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
        self[f"node_base_params/aux_params/aux{index}"] = bus_id

    @property
    def prop_values(self) -> list[Any]:
        """Get the list of initial property values.

        Returns
        -------
        list[Any]
            List of property initial values.
        """
        return self["node_base_params/node_initial_params/prop_initial_values"]

    @property
    def rtpc_count(self) -> int:
        """Get the number of RTPC (real-time parameter control) entries.

        Returns
        -------
        int
            Number of RTPC entries.
        """
        return self["node_base_params/initial_rtpc/count"]

    def clear_rtpcs(self) -> None:
        """Remove all RTPC entries."""
        self["node_base_params/initial_rtpc/rtpcs"] = []
        self["node_base_params/initial_rtpc/count"] = 0
