from pybnk.node import Node
from pybnk.util import PathDict, logger
from .wwise_node import WwiseNode


class MusicSegment(WwiseNode):
    """A timed piece of interactive music with tempo, time signature, and markers.

    Contains music tracks and defines the musical structure for adaptive music systems.
    """

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

        return segment

    @property
    def base_params(self) -> PathDict:
        return PathDict(self["music_node_params/node_base_params"])

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

    def add_child(self, child_id: int | Node) -> None:
        """Associates a child node for random or sequential playback.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance.
        """
        if isinstance(child_id, Node):
            if child_id.parent > 0 and child_id.parent != self.id:
                logger.warning(f"Adding already adopted child {child_id} to {self}")
            
            child_id = child_id.id

        children: list[int] = self["music_node_params/children/items"]
        if child_id not in children:
            children.append(child_id)
            self["music_node_params/children/count"] = len(children)
            children.sort()

    def remove_child(self, child_id: int | Node) -> bool:
        """Disassociates a child node from this container.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance to remove.

        Returns
        -------
        bool
            True if child was removed, False if not found.
        """
        if isinstance(child_id, Node):
            child_id = child_id.id

        children = self["music_node_params/children/items"]
        if child_id in children:
            children.remove(child_id)
            self["music_node_params/children/count"] = len(children)
            return True
        
        return False

    def clear_children(self) -> None:
        """Disassociates all children from this container."""
        self["music_node_params/children/items"] = []
        self["music_node_params/children/count"] = 0

    @property
    def children(self) -> list[int]:
        """Music tracks within this segment.

        Returns
        -------
        list[int]
            List of child track hash IDs.
        """
        return self["music_node_params/children/items"]

    def get_references(self) -> list[tuple[str, int]]:
        paths = (
            "music_node_params/node_base_params/override_bus_id",
            "music_node_params/node_base_params/aux_params/aux1",
            "music_node_params/node_base_params/aux_params/aux2",
            "music_node_params/node_base_params/aux_params/aux3",
            "music_node_params/node_base_params/aux_params/aux4",
        )
        refs = [(p, r) for p in paths if (r := self.get(p, 0)) > 0]

        children = self["music_node_params/children/items"]
        for i, child_id in enumerate(children):
            refs.append(
                (
                    f"music_node_params/children/items:{i}",
                    child_id,
                )
            )

        return refs
