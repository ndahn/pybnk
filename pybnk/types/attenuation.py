from pybnk.node import Node
from pybnk.enums import RtcpType, AccumulationType, ScalingType, CurveType


# NOTE not a BaseNode
class Attenuation(Node):
    """Attenuation object defining distance-based audio falloff curves.

    Controls how sound volume, low-pass filter, high-pass filter, and spread change over distance. Also manages cone-based directional attenuation for focused sound sources.
    """

    @classmethod
    def new(cls, nid: int) -> "Attenuation":
        """Create a new Attenuation node.

        Parameters
        ----------
        nid : int
            Node ID (hash).

        Returns
        -------
        Attenuation
            New Attenuation instance with default volume curve.
        """
        node = cls.from_template(nid, "Attenuation")
        attenuation = cls(node.dict)
        return attenuation

    @property
    def is_cone_enabled(self) -> bool:
        """Get or set whether cone attenuation is enabled.

        Returns
        -------
        bool
            True if cone attenuation is enabled.
        """
        return bool(self["is_cone_enabled"])

    @is_cone_enabled.setter
    def is_cone_enabled(self, value: bool) -> None:
        self["is_cone_enabled"] = int(value)

    @property
    def cone_inside_degrees(self) -> float:
        """Get or set the cone inside angle in degrees.

        Returns
        -------
        float
            Inside cone angle in degrees.
        """
        return self["cone_params/inside_degrees"]

    @cone_inside_degrees.setter
    def cone_inside_degrees(self, value: float) -> None:
        self["cone_params/inside_degrees"] = value

    @property
    def cone_outside_degrees(self) -> float:
        """Get or set the cone outside angle in degrees.

        Returns
        -------
        float
            Outside cone angle in degrees.
        """
        return self["cone_params/outside_degrees"]

    @cone_outside_degrees.setter
    def cone_outside_degrees(self, value: float) -> None:
        self["cone_params/outside_degrees"] = value

    @property
    def cone_outside_volume(self) -> float:
        """Get or set the volume outside the cone.

        Returns
        -------
        float
            Volume attenuation outside cone.
        """
        return self["cone_params/outside_volume"]

    @cone_outside_volume.setter
    def cone_outside_volume(self, value: float) -> None:
        self["cone_params/outside_volume"] = value

    @property
    def curves(self) -> list[dict]:
        """Get the attenuation curves.

        Returns
        -------
        list[dict]
            List of curve dictionaries with scaling, points, and interpolation.
        """
        return self["curves"]

    @property
    def curve_count(self) -> int:
        """Get the number of curves.

        Returns
        -------
        int
            Number of attenuation curves.
        """
        return self["curve_count"]

    @property
    def curves_to_use(self) -> list[int]:
        """Get or set which curves are active.

        Returns
        -------
        list[int]
            Array mapping curve slots to curve indices (-1 = unused).
        """
        return self["curves_to_use"]

    def add_curve(self, curve_scaling: ScalingType = "DB") -> dict:
        """Add a new attenuation curve.

        Parameters
        ----------
        curve_scaling : CurveType, default="DB"
            Scaling type ('DB', 'None', 'Linear').

        Returns
        -------
        dict
            The newly created curve dictionary.
        """
        curve = {"curve_scaling": curve_scaling, "point_count": 0, "points": []}
        self["curves"].append(curve)
        self["curve_count"] = len(self["curves"])
        return curve

    def add_curve_point(
        self,
        curve_index: int,
        from_distance: float,
        to_value: float,
        interpolation: CurveType = "Linear",
    ) -> None:
        """Add a point to an attenuation curve.

        Parameters
        ----------
        curve_index : int
            Index of the curve to modify.
        from_distance : float
            Distance value (x-axis).
        to_value : float
            Output value (y-axis).
        interpolation : CurveType, default="Linear"
            Interpolation type.
        """
        if curve_index < 0 or curve_index >= self.curve_count:
            raise IndexError(f"Curve index {curve_index} out of range")

        point = {"from": from_distance, "to": to_value, "interpolation": interpolation}
        curve = self["curves"][curve_index]
        curve["points"].append(point)
        curve["point_count"] = len(curve["points"])

    def clear_curves(self) -> None:
        """Remove all attenuation curves."""
        self["curves"] = []
        self["curve_count"] = 0

    @property
    def rtpcs(self) -> list[dict]:
        """Get the RTPC (real-time parameter control) entries.

        Returns
        -------
        list[dict]
            List of RTPC dictionaries.
        """
        return self["initial_rtpc/rtpcs"]

    @property
    def rtpc_count(self) -> int:
        """Get the number of RTPC entries.

        Returns
        -------
        int
            Number of RTPCs.
        """
        return self["initial_rtpc/count"]

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

        rtpcs = self["initial_rtpc/rtpcs"]
        rtpcs.append(rtpc)
        self["initial_rtpc/count"] = len(rtpcs)

    def clear_rtpcs(self) -> None:
        """Remove all RTPC entries."""
        self["initial_rtpc/rtpcs"] = []
        self["initial_rtpc/count"] = 0
