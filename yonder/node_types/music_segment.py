from yonder.node import Node
from yonder.util import PathDict, logger
from .wwise_node import WwiseNode
from .mixins import ContainerMixin


class MusicSegment(ContainerMixin, WwiseNode):
    """A timed piece of interactive music with tempo, time signature, and markers.

    Contains music tracks and defines the musical structure for adaptive music systems.
    """
    base_params_path = "music_node_params/node_base_params"
    rtpcs_path = "music_node_params/node_base_params/initial_rtpc"
    children_path = "music_node_params/children"
    

    @classmethod
    def new(
        cls,
        nid: int,
        duration: float = 0.0,
        parent: int | Node = None,
    ) -> "MusicSegment":
        """Create a new MusicSegment node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        duration : float, default=0.0
            Segment duration in milliseconds.
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        MusicSegment
            New MusicSegment instance.
        """
        temp = cls.load_template(cls.__name__)

        segment = cls(temp)
        segment.id = nid
        segment.duration = duration
        if parent is not None:
            segment.parent = parent

        logger.info(f"Created new node {segment}")
        return segment

    @property
    def music_params(self) -> PathDict:
        return PathDict(self["music_node_params"])

    @property
    def duration(self) -> float:
        """Segment duration in milliseconds.

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
    def markers(self) -> list[dict]:
        """Timing markers for synchronization and transitions within the segment.

        Returns
        -------
        list[dict]
            List of marker dictionaries with id, position, and string.
        """
        return self["markers"]

    def add_marker(self, marker_id: int, position: float, name: str = "") -> None:
        """Places a timing marker at a specific position within the segment.

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
            "string_length": len(name) + 1 if name else 0,
            "string": name,
        }
        self["markers"].append(marker)
        self["marker_count"] = len(self["markers"])

    def remove_marker(self, marker_id: int) -> bool:
        """Removes a timing marker from the segment.

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
        """Removes all timing markers from the segment."""
        self["markers"] = []
        self["marker_count"] = 0
