from pybnk.node import Node
from pybnk.enums import SourceType
from .wwise_node import WwiseNode


class MusicTrack(WwiseNode):
    """An individual audio track within a music segment.

    Contains the actual audio sources and defines when/how they play within the segment timeline.
    """

    @classmethod
    def new(
        cls,
        nid: int,
        source_id: int = None,
        plugin: str = "VORBIS",
        source_type: str = "Streaming",
        parent: int | Node = None,
    ) -> "MusicTrack":
        """Create a new MusicTrack node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        source_id : int
            Media source ID.
        plugin : str, default="VORBIS"
            Codec plugin ('VORBIS', 'PCM', etc.).
        source_type : str, default="Streaming"
            Source type ('Streaming' or 'Embedded').
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        MusicTrack
            New MusicTrack instance.
        """
        temp = cls.load_template(cls.__name__)

        track = cls(temp)
        track.id = nid
        if source_id is not None:
            track.add_source(source_id, source_type, plugin)
            track.add_playlist_item(source_id)

        if parent is not None:
            track.parent = parent

        return track

    @property
    def track_type(self) -> int:
        """Track type.

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
        """Look-ahead time in milliseconds.

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
        """Number of subtracks.

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
        """Audio files used by this track.

        Returns
        -------
        list[dict]
            List of source dictionaries with plugin, source_type, and media_information.
        """
        return self["sources"]

    @property
    def playlist(self) -> list[dict]:
        """Timing and playback configuration for sources on the timeline.

        Returns
        -------
        list[dict]
            List of playlist item dictionaries.
        """
        return self["playlist"]

    def add_source(
        self,
        source_id: int,
        source_type: SourceType = "Embedded",
        plugin: str = "VORBIS",
        media_size: int = 0,
    ) -> None:
        """Associates an audio file with this track.

        Parameters
        ----------
        source_id : int
            Media source ID.
        source_type : SourceType
            Source type.
        plugin : str
            Codec plugin.
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
        """Schedules a source to play at a specific time on the track timeline.

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
        """Disassociates all audio sources from this track."""
        self["sources"] = []
        self["source_count"] = 0

    def clear_playlist(self) -> None:
        """Clears the track timeline, removing all scheduled playback items."""
        self["playlist"] = []
        self["playlist_item_count"] = 0