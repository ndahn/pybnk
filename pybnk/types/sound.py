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
        source_type: str = "Embedded",
        parent_id: int = 0,
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
        source_type : str, default="Embedded"
            Source type ('Embedded' or 'Streamed').
        parent_id : int, default=0
            Parent node ID.

        Returns
        -------
        Sound
            New Sound instance.
        """
        node = cls.from_template(nid, "Sound")

        sound = cls(node.dict)
        sound.source_id = source_id
        sound.plugin = plugin
        sound.source_type = source_type
        if parent_id != 0:
            sound.parent = parent_id

        return sound

    @property
    def source_id(self) -> int:
        """Get or set the media source ID.

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
        """Get or set the codec plugin type.

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
    def source_type(self) -> str:
        """Get or set the source type.

        Returns
        -------
        str
            Source type (e.g., 'Embedded', 'Streamed').
        """
        return self["bank_source_data/source_type"]

    @source_type.setter
    def source_type(self, value: str) -> None:
        self["bank_source_data/source_type"] = value

    @property
    def media_size(self) -> int:
        """Get or set the in-memory media size in bytes.

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
    def is_streamed(self) -> bool:
        """Check if the sound is streamed from disk.

        Returns
        -------
        bool
            True if streamed, False if embedded.
        """
        return self.source_type == "Streamed"

    @property
    def is_embedded(self) -> bool:
        """Check if the sound is embedded in the bank.

        Returns
        -------
        bool
            True if embedded, False if streamed.
        """
        return self.source_type == "Embedded"

    @property
    def enable_attenuation(self) -> bool:
        """Get or set whether 3D attenuation is enabled.

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
        """Get or set the 3D spatialization mode.

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
        """Set the sound to be streamed or embedded.

        Parameters
        ----------
        streamed : bool, default=True
            If True, set to streamed; if False, set to embedded.
        """
        self.source_type = "Streamed" if streamed else "Embedded"
