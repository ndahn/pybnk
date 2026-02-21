from .wwise_node import WwiseNode


class MusicRandomSequenceContainer(WwiseNode):
    """ Interactive music playlist that randomly or sequentially plays music segments. 
    
    Includes transition rules for smooth musical transitions and weighted selection for segments.
    """

    @property
    def tempo(self) -> float:
        """Get or set the tempo in BPM.

        Returns
        -------
        float
            Tempo in beats per minute.
        """
        return self["music_trans_node_params/music_node_params/meter_info/tempo"]

    @tempo.setter
    def tempo(self, value: float) -> None:
        self["music_trans_node_params/music_node_params/meter_info/tempo"] = value

    @property
    def time_signature(self) -> tuple[int, int]:
        """Get or set the time signature.

        Returns
        -------
        tuple[int, int]
            (beat_count, beat_value) e.g., (4, 4) for 4/4 time.
        """
        beat_count = self[
            "music_trans_node_params/music_node_params/meter_info/time_signature_beat_count"
        ]
        beat_value = self[
            "music_trans_node_params/music_node_params/meter_info/time_signature_beat_value"
        ]
        return (beat_count, beat_value)

    @time_signature.setter
    def time_signature(self, value: tuple[int, int]) -> None:
        beat_count, beat_value = value
        self[
            "music_trans_node_params/music_node_params/meter_info/time_signature_beat_count"
        ] = beat_count
        self[
            "music_trans_node_params/music_node_params/meter_info/time_signature_beat_value"
        ] = beat_value

    @property
    def grid_period(self) -> float:
        """Get or set the grid period in milliseconds.

        Returns
        -------
        float
            Grid period in ms.
        """
        return self["music_trans_node_params/music_node_params/meter_info/grid_period"]

    @grid_period.setter
    def grid_period(self, value: float) -> None:
        self["music_trans_node_params/music_node_params/meter_info/grid_period"] = value

    @property
    def playlist_items(self) -> list[dict]:
        """Get the playlist items.

        Returns
        -------
        list[dict]
            List of playlist item dictionaries with segment_id, weight, and loop settings.
        """
        return self["playlist_items"]

    @property
    def playlist_item_count(self) -> int:
        """Get the number of playlist items.

        Returns
        -------
        int
            Number of items in the playlist.
        """
        return self["playlist_item_count"]

    @property
    def transition_rules(self) -> list[dict]:
        """Get the transition rules.

        Returns
        -------
        list[dict]
            List of transition rule dictionaries.
        """
        return self["music_trans_node_params/transition_rules"]

    @property
    def transition_rule_count(self) -> int:
        """Get the number of transition rules.

        Returns
        -------
        int
            Number of transition rules.
        """
        return self["music_trans_node_params/transition_rule_count"]

    @property
    def children_ids(self) -> list[int]:
        """Get list of child segment IDs.

        Returns
        -------
        list[int]
            List of child segment hash IDs.
        """
        return self["music_trans_node_params/music_node_params/children/items"]

    def add_playlist_item(
        self,
        segment_id: int,
        playlist_item_id: int,
        weight: int = 50000,
        avoid_repeat: int = 0,
    ) -> None:
        """Add a playlist item to the container.

        Parameters
        ----------
        segment_id : int
            Segment node ID.
        playlist_item_id : int
            Unique playlist item ID.
        weight : int, default=50000
            Relative weight for random selection.
        avoid_repeat : int, default=0
            Number of recent items to avoid repeating.
        """
        item = {
            "segment_id": segment_id,
            "playlist_item_id": playlist_item_id,
            "child_count": 0,
            "ers_type": 0,
            "loop_base": 0,
            "loop_min": 0,
            "loop_max": 0,
            "weight": weight,
            "avoid_repeat_count": avoid_repeat,
            "use_weight": 0,
            "shuffle": 0,
        }
        self["playlist_items"].append(item)
        self["playlist_item_count"] = len(self["playlist_items"])

    def remove_playlist_item(self, playlist_item_id: int) -> bool:
        """Remove a playlist item by its ID.

        Parameters
        ----------
        playlist_item_id : int
            Playlist item ID to remove.

        Returns
        -------
        bool
            True if item was removed, False if not found.
        """
        items = self["playlist_items"]
        for i, item in enumerate(items):
            if item["playlist_item_id"] == playlist_item_id:
                items.pop(i)
                self["playlist_item_count"] = len(items)
                return True
        return False

    def clear_playlist(self) -> None:
        """Remove all playlist items from the container."""
        self["playlist_items"] = []
        self["playlist_item_count"] = 0
