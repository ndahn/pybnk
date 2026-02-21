from .wwise_node import WwiseNode


class MusicTrack(WwiseNode):
    """An individual audio track within a music segment. Contains the actual audio sources and defines when/how they play within the segment timeline.
    """

    @property
    def track_type(self) -> int:
        """Get or set the track type.

        Returns
        -------
        int
            Track type identifier.
        """
        return self["track_type"]

    @track_type.setter
    def track_type(self, value: int) -> None:
        self["track_type"] = value

    @property
    def look_ahead_time(self) -> int:
        """Get or set the look-ahead time in milliseconds.

        Returns
        -------
        int
            Look-ahead time in ms.
        """
        return self["look_ahead_time"]

    @look_ahead_time.setter
    def look_ahead_time(self, value: int) -> None:
        self["look_ahead_time"] = value

    @property
    def subtrack_count(self) -> int:
        """Get or set the number of subtracks.

        Returns
        -------
        int
            Number of subtracks.
        """
        return self["subtrack_count"]

    @subtrack_count.setter
    def subtrack_count(self, value: int) -> None:
        self["subtrack_count"] = value

    @property
    def sources(self) -> list[dict]:
        """Get the list of audio sources.

        Returns
        -------
        list[dict]
            List of source dictionaries with plugin, source_type, and media_information.
        """
        return self["sources"]

    @property
    def source_count(self) -> int:
        """Get the number of sources.

        Returns
        -------
        int
            Number of sources in the track.
        """
        return self["source_count"]

    @property
    def playlist(self) -> list[dict]:
        """Get the playlist items.

        Returns
        -------
        list[dict]
            List of playlist item dictionaries.
        """
        return self["playlist"]

    @property
    def playlist_item_count(self) -> int:
        """Get the number of playlist items.

        Returns
        -------
        int
            Number of playlist items.
        """
        return self["playlist_item_count"]

    def add_source(
        self, plugin: str, source_type: str, source_id: int, media_size: int = 0
    ) -> None:
        """Add an audio source to the track.

        Parameters
        ----------
        plugin : str
            Codec plugin (e.g., 'VORBIS', 'PCM').
        source_type : str
            Source type (e.g., 'Streaming', 'Embedded').
        source_id : int
            Media source ID.
        media_size : int, default=0
            In-memory media size in bytes.
        """
        source = {
            "plugin": plugin,
            "source_type": source_type,
            "media_information": {
                "source_id": source_id,
                "in_memory_media_size": media_size,
                "source_flags": 0,
            },
            "params_size": 0,
            "params": "",
        }
        self["sources"].append(source)
        self["source_count"] = len(self["sources"])

    def add_playlist_item(
        self,
        source_id: int,
        play_at: float = 0.0,
        source_duration: float = 0.0,
        begin_trim: float = 0.0,
        end_trim: float = 0.0,
    ) -> None:
        """Add a playlist item to the track.

        Parameters
        ----------
        source_id : int
            Source ID to play.
        play_at : float, default=0.0
            Start time in milliseconds.
        source_duration : float, default=0.0
            Duration in milliseconds.
        begin_trim : float, default=0.0
            Trim offset from beginning in ms.
        end_trim : float, default=0.0
            Trim offset from end in ms.
        """
        item = {
            "track_id": 0,
            "source_id": source_id,
            "event_id": 0,
            "play_at": play_at,
            "begin_trim_offset": begin_trim,
            "end_trim_offset": end_trim,
            "source_duration": source_duration,
        }
        self["playlist"].append(item)
        self["playlist_item_count"] = len(self["playlist"])

    def clear_sources(self) -> None:
        """Remove all sources from the track."""
        self["sources"] = []
        self["source_count"] = 0

    def clear_playlist(self) -> None:
        """Remove all playlist items from the track."""
        self["playlist"] = []
        self["playlist_item_count"] = 0
