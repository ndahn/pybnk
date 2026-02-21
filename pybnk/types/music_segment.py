from .wwise_node import WwiseNode


class MusicSegment(WwiseNode):
    """A timed piece of interactive music with tempo, time signature, and markers. Contains music tracks and defines the musical structure for adaptive music systems.
    """

    @property
    def duration(self) -> float:
        """Get or set the segment duration in milliseconds.

        Returns
        -------
        float
            Duration in ms.
        """
        return self["duration"]

    @duration.setter
    def duration(self, value: float) -> None:
        self["duration"] = value

    @property
    def tempo(self) -> float:
        """Get or set the tempo in BPM.

        Returns
        -------
        float
            Tempo in beats per minute.
        """
        return self["music_node_params/meter_info/tempo"]

    @tempo.setter
    def tempo(self, value: float) -> None:
        self["music_node_params/meter_info/tempo"] = value

    @property
    def time_signature(self) -> tuple[int, int]:
        """Get or set the time signature.

        Returns
        -------
        tuple[int, int]
            (beat_count, beat_value) e.g., (4, 4) for 4/4 time.
        """
        beat_count = self["music_node_params/meter_info/time_signature_beat_count"]
        beat_value = self["music_node_params/meter_info/time_signature_beat_value"]
        return (beat_count, beat_value)

    @time_signature.setter
    def time_signature(self, value: tuple[int, int]) -> None:
        beat_count, beat_value = value
        self["music_node_params/meter_info/time_signature_beat_count"] = beat_count
        self["music_node_params/meter_info/time_signature_beat_value"] = beat_value

    @property
    def grid_period(self) -> float:
        """Get or set the grid period in milliseconds.

        Returns
        -------
        float
            Grid period in ms.
        """
        return self["music_node_params/meter_info/grid_period"]

    @grid_period.setter
    def grid_period(self, value: float) -> None:
        self["music_node_params/meter_info/grid_period"] = value

    @property
    def markers(self) -> list[dict]:
        """Get the list of markers.

        Returns
        -------
        list[dict]
            List of marker dictionaries with id, position, and string.
        """
        return self["markers"]

    @property
    def marker_count(self) -> int:
        """Get the number of markers.

        Returns
        -------
        int
            Number of markers in the segment.
        """
        return self["marker_count"]

    def add_marker(self, marker_id: int, position: float, name: str = "") -> None:
        """Add a marker to the segment.

        Parameters
        ----------
        marker_id : int
            Unique marker ID.
        position : float
            Position in milliseconds.
        name : str, default=""
            Optional marker name.
        """
        marker = {
            "id": marker_id,
            "position": position,
            "string_length": len(name),
            "string": name,
        }
        self["markers"].append(marker)
        self["marker_count"] = len(self["markers"])

    def remove_marker(self, marker_id: int) -> bool:
        """Remove a marker by ID.

        Parameters
        ----------
        marker_id : int
            Marker ID to remove.

        Returns
        -------
        bool
            True if marker was removed, False if not found.
        """
        markers = self["markers"]
        for i, marker in enumerate(markers):
            if marker["id"] == marker_id:
                markers.pop(i)
                self["marker_count"] = len(markers)
                return True
        return False

    def clear_markers(self) -> None:
        """Remove all markers from the segment."""
        self["markers"] = []
        self["marker_count"] = 0

    @property
    def children_ids(self) -> list[int]:
        """Get list of child track IDs.

        Returns
        -------
        list[int]
            List of child track hash IDs.
        """
        return self["music_node_params/children/items"]
