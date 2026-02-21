from pybnk.node import Node


# NOTE not a BaseNode
class Attenuation(Node):
    """Attenuation object defining distance-based audio falloff curves. 
    
    Controls how sound volume, low-pass filter, high-pass filter, and spread change over distance. Also manages cone-based directional attenuation for focused sound sources.
    """

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

    def add_curve(self, curve_scaling: str = "DB") -> dict:
        """Add a new attenuation curve.

        Parameters
        ----------
        curve_scaling : str, default="DB"
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
        interpolation: str = "Linear",
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
        interpolation : str, default="Linear"
            Interpolation type ('Linear', 'SCurve', 'Log1', 'Sine', etc.).
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
