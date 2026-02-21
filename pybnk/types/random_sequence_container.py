from pybnk.node import Node
from .wwise_node import WwiseNode


class RandomSequenceContainer(WwiseNode):
    """Plays its children either randomly or in sequence.

    Supports looping, transition timing, and avoiding recent repeats. Used for variations (footsteps, gunshots, voice lines).
    """

    @classmethod
    def new(
        cls, nid: int, mode: int = 0, loop_count: int = 1, parent_id: int = 0
    ) -> "RandomSequenceContainer":
        """Create a new RandomSequenceContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        mode : int, default=0
            Playback mode (0 = Random, 1 = Sequence).
        loop_count : int, default=1
            Number of loops (0 = infinite).
        parent_id : int, default=0
            Parent node ID.

        Returns
        -------
        RandomSequenceContainer
            New RandomSequenceContainer instance.
        """
        node = cls.from_template(nid, "RandomSequenceContainer")

        container = cls(node.dict)
        container.mode = mode
        container.loop_count = loop_count
        if parent_id != 0:
            container.parent = parent_id

        return container

    @property
    def loop_count(self) -> int:
        """Get or set the number of times the container loops.

        Returns
        -------
        int
            Loop count (0 = infinite).
        """
        return self["loop_count"]

    @loop_count.setter
    def loop_count(self, value: int) -> None:
        self["loop_count"] = value

    @property
    def transition_time(self) -> float:
        """Get or set the transition time in milliseconds.

        Returns
        -------
        float
            Transition time between children in ms.
        """
        return self["transition_time"]

    @transition_time.setter
    def transition_time(self, value: float) -> None:
        self["transition_time"] = value

    @property
    def avoid_repeat_count(self) -> int:
        """Get or set how many recent items to avoid repeating.

        Returns
        -------
        int
            Number of recent children to avoid.
        """
        return self["avoid_repeat_count"]

    @avoid_repeat_count.setter
    def avoid_repeat_count(self, value: int) -> None:
        self["avoid_repeat_count"] = value

    @property
    def mode(self) -> int:
        """Get or set the playback mode.

        Returns
        -------
        int
            0 = Random, 1 = Sequence.
        """
        return self["mode"]

    @mode.setter
    def mode(self, value: int) -> None:
        self["mode"] = value

    @property
    def children_ids(self) -> list[int]:
        """Get list of child node IDs.

        Returns
        -------
        list[int]
            List of child node hash IDs.
        """
        return self["children/items"]

    def add_child(self, child_id: int | Node) -> None:
        """Add a child node to the container.

        Parameters
        ----------
        child_id : int | Node
            Child node ID or Node instance.
        """
        if isinstance(child_id, Node):
            child_id = child_id.id

        children: list[int] = self["children/items"]
        if child_id not in children:
            children.append(child_id)
            self["children/count"] = len(children)
            children.sort()

    def remove_child(self, child_id: int | Node) -> bool:
        """Remove a child node from the container.

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

        children = self["children/items"]
        if child_id in children:
            children.remove(child_id)
            self["children/count"] = len(children)
            return True
        return False

    def clear_children(self) -> None:
        """Remove all children from the container."""
        self["children/items"] = []
        self["children/count"] = 0

    @property
    def playlist_ids(self) -> list[int]:
        """Get list of playlist item IDs.

        Returns
        -------
        list[int]
            List of playlist item hash IDs.
        """
        return self["playlist/items"]

    def add_to_playlist(self, item_id: int | Node) -> None:
        """Add an item to the playlist.

        Parameters
        ----------
        item_id : int | Node
            Item ID or Node instance.
        """
        if isinstance(item_id, Node):
            item_id = item_id.id

        playlist = self["playlist/items"]
        if item_id not in playlist:
            playlist.append(item_id)
            self["playlist/count"] = len(playlist)
