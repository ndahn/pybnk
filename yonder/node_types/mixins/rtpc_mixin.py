from typing import TYPE_CHECKING
from yonder.enums import RtpcType, AccumulationType, ScalingType, CurveType

if TYPE_CHECKING:
    from yonder.node import Node


class RtpcMixin:
    rtpcs_path = "initial_rtpc"


    @property
    def rtpcs(self) -> list[dict]:
        """Real-time parameter controls for dynamic audio property adjustments.

        Returns
        -------
        list[dict]
            List of RTPC dictionaries.
        """
        return self[f"{self.rtpcs_path}/rtpcs"]

    def add_rtpc(
        self,
        rtpc_id: int,
        param_id: int,
        curve_id: "int | Node",
        graph_points: list[tuple[float, float, CurveType]] = None,
        rtpc_type: RtpcType = "GameParameter",
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
        from yonder.node import Node

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

        self.rtpcs.append(rtpc)
        self[f"{self.rtpcs_path}/count"] = len(self.rtpcs)

    def clear_rtpcs(self) -> None:
        """Remove all RTPC entries."""
        self.rtpcs.clear()
        self[f"{self.rtpcs_path}/count"] = 0

    def get_references(self) -> list[tuple[str, int]]:
        refs = super().get_references()

        for i, rtpc in enumerate(self.rtpcs):
            refs.append(
                f"{self.rtpcs_path}/rtpcs:{i}/id",
                rtpc["id"],
            )
            if rtpc["curve_id"] > 0:
                refs.append(
                    (
                        f"{self.rtpcs_path}/rtpcs:{i}/curve_id",
                        rtpc["curve_id"],
                    )
                )

        return refs
