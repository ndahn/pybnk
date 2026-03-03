from pybnk.node import Node
from pybnk.util import logger
from .wwise_node import WwiseNode


class MusicRandomSequenceContainer(WwiseNode):
    """Interactive music playlist that randomly or sequentially plays music segments.

    Includes transition rules for smooth musical transitions and weighted selection for segments.
    """

    @classmethod
    def new(
        cls,
        nid: int,
        tempo: float = 120.0,
        time_signature: tuple[int, int] = (4, 4),
        parent: int | Node = None,
    ) -> "MusicRandomSequenceContainer":
        """Create a new MusicRandomSequenceContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        tempo : float, default=120.0
            Tempo in BPM.
        time_signature : tuple[int, int], default=(4, 4)
            Time signature (beat_count, beat_value).
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        MusicRandomSequenceContainer
            New MusicRandomSequenceContainer instance.
        """
        temp = cls.load_template(cls.__name__)

        container = cls(temp)
        container.id = nid
        container.tempo = tempo
        container.time_signature = time_signature
        if parent is not None:
            container.parent = parent

        return container

    @property
    def tempo(self) -> float:
        """Tempo in BPM.

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
        """Time signature.

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
        """Grid period in milliseconds.

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
        """Segments in the playlist with their weights and loop settings.

        Returns
        -------
        list[dict]
            List of playlist item dictionaries with segment_id, weight, and loop settings.
        """
        return self["playlist_items"]

    @property
    def transition_rules(self) -> list[dict]:
        """Rules defining musical transitions between segments.

        Returns
        -------
        list[dict]
            List of transition rule dictionaries.
        """
        return self["music_trans_node_params/transition_rules"]

    @property
    def children_ids(self) -> list[int]:
        """Music segments available for playback in this container.

        Returns
        -------
        list[int]
            List of child segment hash IDs.
        """
        return self["music_trans_node_params/music_node_params/children/items"]

    def add_playlist_item(
        self,
        segment_id: int | Node,
        playlist_item_id: int,
        weight: int = 50000,
        avoid_repeat: int = 0,
    ) -> None:
        """Associates a segment with this playlist for random/sequential playback.

        Parameters
        ----------
        segment_id : int | Node
            Segment node ID.
        playlist_item_id : int
            Unique playlist item ID.
        weight : int, default=50000
            Relative weight for random selection.
        avoid_repeat : int, default=0
            Number of recent items to avoid repeating.
        """
        if isinstance(segment_id, Node):
            if segment_id.parent > 0 and segment_id.parent != self.id:
                logger.warning(f"Adding already adopted child {segment_id} to {self}")
            
            segment_id = segment_id.id

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

    def remove_playlist_item(self, playlist_item_id: int | Node) -> bool:
        """Disassociates a playlist item from this container.

        Parameters
        ----------
        playlist_item_id : int
            Playlist item ID to remove.

        Returns
        -------
        bool
            True if item was removed, False if not found.
        """
        if isinstance(playlist_item_id, Node):
            playlist_item_id = playlist_item_id.id
        
        items = self["playlist_items"]
        for i, item in enumerate(items):
            if item["playlist_item_id"] == playlist_item_id:
                items.pop(i)
                self["playlist_item_count"] = len(items)
                return True
        
        return False

    def clear_playlist(self) -> None:
        """Disassociates all playlist items from this container."""
        self["playlist_items"] = []
        self["playlist_item_count"] = 0