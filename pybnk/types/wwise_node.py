from pybnk.node import Node
from pybnk.enums import RtcpType, AccumulationType, ScalingType, CurveType
from pybnk.util import logger


class WwiseNode(Node):
    """Base class for nodes with common node_base_params functionality.

    Provides convenient access to shared parameters like aux sends, virtual voice behavior, and state management.
    """

    @property
    def properties(self) -> dict[str, float]:
        """Initial property values.

        Returns
        -------
        dict[str, float]
            Dict of property initial values.
        """
        node_properties = self["node_base_params/node_initial_params/prop_initial_values"]
        # Much easier to manage
        properties = {}

        for d in node_properties:
            if len(d) != 1:
                logger.error(f"Don't know how to handle property {d}")
                continue

            key = next(k for k in d.keys())
            properties[key] = d[key]

        return properties

    def get_property(self, prop_name: str, default: float = None) -> float:
        """Get a property value by name.

        Parameters
        ----------
        prop_name : str
            Property name (e.g., 'Volume', 'Pitch', 'LPF', 'HPF').
        default : float, optional
            Default value if property not found.

        Returns
        -------
        float
            Property value, or default if not found.
        """
        return self.properties.get(prop_name, default)

    def set_property(self, prop_name: str, value: float) -> None:
        """Set a property value by name.

        If the property already exists, updates it. Otherwise, adds it.

        Parameters
        ----------
        prop_name : str
            Property name (e.g., 'Volume', 'Pitch', 'LPF', 'HPF').
        value : float
            Property value to set.
        """
        # Try to find and update existing property
        node_properties = self["node_base_params/node_initial_params/prop_initial_values"]
        for prop_dict in node_properties:
            if prop_name in prop_dict:
                prop_dict[prop_name] = value
                return

        # Property doesn't exist, add it
        node_properties.append({prop_name: value})

    def remove_property(self, prop_name: str) -> bool:
        """Remove a property by name.

        Parameters
        ----------
        prop_name : str
            Property name to remove.

        Returns
        -------
        bool
            True if property was removed, False if not found.
        """
        prop_values = self["node_base_params/node_initial_params/prop_initial_values"]
        for i, prop_dict in enumerate(prop_values):
            if prop_name in prop_dict:
                prop_values.pop(i)
                return True
        return False

    def clear_properties(self) -> None:
        """Remove all initial property values."""
        self["node_base_params/node_initial_params/prop_initial_values"] = []

    # Convenience properties for common parameters
    @property
    def volume(self) -> float:
        """Volume in dB.

        Returns
        -------
        float
            Volume offset in dB (default 0.0 if not set).
        """
        return self.get_property("Volume", 0.0)

    @volume.setter
    def volume(self, value: float) -> None:
        self.set_property("Volume", value)

    @property
    def pitch(self) -> float:
        """Pitch in cents.

        Returns
        -------
        float
            Pitch offset in cents (default 0.0 if not set).
        """
        return self.get_property("Pitch", 0.0)

    @pitch.setter
    def pitch(self, value: float) -> None:
        self.set_property("Pitch", value)

    @property
    def lowpass_filter(self) -> float:
        """Low-pass filter value.

        Returns
        -------
        float
            LPF value (default 0.0 if not set).
        """
        return self.get_property("LPF", 0.0)

    @lowpass_filter.setter
    def lowpass_filter(self, value: float) -> None:
        self.set_property("LPF", value)

    @property
    def highpass_filter(self) -> float:
        """High-pass filter value.

        Returns
        -------
        float
            HPF value (default 0.0 if not set).
        """
        return self.get_property("HPF", 0.0)

    @highpass_filter.setter
    def highpass_filter(self, value: float) -> None:
        self.set_property("HPF", value)

    @property
    def attenuation_id(self) -> int:
        """Attenuation ID reference.

        Returns
        -------
        int
            Attenuation node ID (default 0 if not set).
        """
        return int(self.get_property("AttenuationID", 0))

    @attenuation_id.setter
    def attenuation_id(self, value: int) -> None:
        self.set_property("AttenuationID", float(value))

    @property
    def max_instances(self) -> int:
        """Maximum number of concurrent instances.

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
        """Whether virtual voice behavior is enabled.

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
        """Virtual voice queue behavior.

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
        """Whether auxiliary sends are enabled.

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

    def add_rtpc(
        self,
        rtpc_id: int,
        param_id: int,
        curve_id: int | Node,
        graph_points: list[tuple[float, float, CurveType]] = None,
        rtpc_type: RtcpType = "GameParameter",
        rtpc_accum: AccumulationType = "Additive",
        curve_scaling: ScalingType = "DB",
    ) -> None:
        """Add an RTPC (Real-Time Parameter Control) entry.

        Parameters
        ----------
        rtpc_id : int
            RTPC identifier (game parameter ID).
        param_id : int
            Parameter to control (0=Volume, 2=LPF, 3=Pitch, 5=BusVolume, etc.).
        curve_id : int | Node
            Curve identifier for this RTPC.
        graph_points : list[tuple[float, float, CurveType]], optional
            List of (from, to, interpolation) tuples for the curve.
            Defaults to a linear 0->-1, 1->0 curve if not provided.
        rtpc_type : RtcpType, default="GameParameter"
            RTPC type.
        rtpc_accum : AccumulationType, default="Additive"
            Accumulation mode.
        curve_scaling : ScalingType, default="DB"
            Curve scaling type ('DB', 'Linear', 'None').
        """
        if isinstance(curve_id, Node):
            curve_id = curve_id.id

        if graph_points is None:
            graph_points = [(0.0, -1.0, "Linear"), (1.0, 0.0, "Linear")]

        rtpc = {
            "id": rtpc_id,
            "rtpc_type": rtpc_type,
            "rtpc_accum": rtpc_accum,
            "param_id": param_id,
            "curve_id": curve_id,
            "curve_scaling": curve_scaling,
            "graph_point_count": len(graph_points),
            "graph_points": [
                {"from": from_val, "to": to_val, "interpolation": interp}
                for from_val, to_val, interp in graph_points
            ],
        }

        rtpcs = self["node_base_params/initial_rtpc/rtpcs"]
        rtpcs.append(rtpc)
        self["node_base_params/initial_rtpc/count"] = len(rtpcs)

    def clear_rtpcs(self) -> None:
        """Remove all RTPC entries."""
        self["node_base_params/initial_rtpc/rtpcs"] = []
        self["node_base_params/initial_rtpc/count"] = 0
