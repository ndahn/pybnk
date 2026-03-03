import os
from pathlib import Path

from pybnk.node import Node
from pybnk.enums import SourceType
from .wwise_node import WwiseNode



class Sound(WwiseNode):
    """The fundamental playable audio object.

    Contains a single audio file (embedded or streamed) with codec settings and 3D positioning parameters.
    """

    @classmethod
    def new(
        cls,
        nid: int,
        source_id: int,
        plugin: str = "VORBIS",
        source_type: SourceType = "Embedded",
        parent: int | Node = None,
    ) -> "Sound":
        """Create a new Sound node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        source_id : int
            Media source ID.
        plugin : str, default="VORBIS"
            Codec plugin ('VORBIS', 'PCM', etc.).
        source_type : SourceType, default="Embedded"
            Source type ('Embedded' or 'Streamed').
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        Sound
            New Sound instance.
        """
        temp = cls.load_template(cls.__name__)

        sound = cls(temp)
        sound.id = nid
        sound.source_id = source_id
        sound.plugin = plugin
        sound.source_type = source_type
        if parent is not None:
            sound.parent = parent

        return sound

    @classmethod
    def new_from_wem(
        cls,
        nid: int,
        wem: Path,
        mode: SourceType = "Embedded",
        parent: int | Node = None,
    ) -> "Sound":
        wem_id = int(wem.name.rsplit(".")[0])
        size = os.path.getsize(str(wem))

        if mode == "Embedded":
            pass
        elif mode == "Streaming":
            # TODO not used in ER I think?
            pass
        elif mode == "PrefetchStreaming":
            # TODO create prefetch snippet
            pass

        # TODO source duration (in ms)
        # https://docs.google.com/document/d/1Dx8U9q6iEofPtKtZ0JI1kOedJYs9ifhlO7H5Knil5sg/edit?tab=t.0
        # https://discord.com/channels/529802828278005773/1252503668515934249

        sound = cls.new(nid, wem_id)
        sound.media_size = size
        if parent is not None:
            sound.parent = parent
        
        return sound

    @property
    def source_id(self) -> int:
        """Media source ID.

        Returns
        -------
        int
            Source ID referencing the audio data.
        """
        return self["bank_source_data/media_information/source_id"]

    @source_id.setter
    def source_id(self, value: int) -> None:
        self["bank_source_data/media_information/source_id"] = value

    @property
    def plugin(self) -> str:
        """Codec plugin type.

        Returns
        -------
        str
            Plugin name (e.g., 'VORBIS', 'PCM').
        """
        return self["bank_source_data/plugin"]

    @plugin.setter
    def plugin(self, value: str) -> None:
        self["bank_source_data/plugin"] = value

    @property
    def source_type(self) -> SourceType:
        """Source type.

        Returns
        -------
 SourceTyper
            Source type (e.g., 'Embedded', 'Streamed').
        """
        return self["bank_source_data/source_type"]

    @source_type.setter
    def source_type(self, value: SourceType) -> None:
        self["bank_source_data/source_type"] = value

    @property
    def media_size(self) -> int:
        """In-memory media size in bytes.

        Returns
        -------
        int
            Size of audio data in bytes.
        """
        return self["bank_source_data/media_information/in_memory_media_size"]

    @media_size.setter
    def media_size(self, value: int) -> None:
        self["bank_source_data/media_information/in_memory_media_size"] = value

    @property
    def enable_attenuation(self) -> bool:
        """Controls whether distance-based volume falloff is applied.

        Returns
        -------
        bool
            True if attenuation is enabled.
        """
        return self["node_base_params/positioning_params/enable_attenuation"]

    @enable_attenuation.setter
    def enable_attenuation(self, value: bool) -> None:
        self["node_base_params/positioning_params/enable_attenuation"] = value

    @property
    def three_dimensional_spatialization(self) -> str:
        """Controls how positional audio is rendered in 3D space.

        Returns
        -------
        str
            Spatialization mode (e.g., 'None', 'Position', 'PositionAndOrientation').
        """
        return self[
            "node_base_params/positioning_params/three_dimensional_spatialization_mode"
        ]

    @three_dimensional_spatialization.setter
    def three_dimensional_spatialization(self, value: str) -> None:
        self[
            "node_base_params/positioning_params/three_dimensional_spatialization_mode"
        ] = value

    def set_streaming(self, streamed: bool = True) -> None:
        """Configures whether audio loads into memory or streams from disk.

        Parameters
        ----------
        streamed : bool, default=True
            If True, set to streamed; if False, set to embedded.
        """
        self.source_type = "Streamed" if streamed else "Embedded"