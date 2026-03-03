from pybnk.node import Node
from pybnk.util import logger
from .wwise_node import WwiseNode


class RandomSequenceContainer(WwiseNode):
    """Plays its children either randomly or in sequence.

    Supports looping, transition timing, and avoiding recent repeats. Used for variations (footsteps, gunshots, voice lines).
    """

    @classmethod
    def new(
        cls, nid: int, avoid_repeats: bool = False, loop_count: int = 1, parent: int | Node = None
    ) -> "RandomSequenceContainer":
        """Create a new RandomSequenceContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        avoid_repeats : bool, default=False
            If True this RSC will avoid playing the same child twice in a row.
        loop_count : int, default=1
            Number of loops (0 = infinite).
        parent : int | Node, default=None
            Parent node.

        Returns
        -------
        RandomSequenceContainer
            New RandomSequenceContainer instance.
        """
        temp = cls.load_template(cls.__name__)

        container = cls(temp)
        container.id = nid
        container.avoid_repeats = avoid_repeats
        container.loop_count = loop_count
        if parent is not None:
            container.parent = parent

        return container

    @property
    def loop_count(self) -> int:
        """Number of times the container loops.

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
        """Transition time in milliseconds.

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
    def avoid_repeats(self) -> bool:
        """Controls whether the same child can play consecutively.

        Returns
        -------
        bool
            True if playing the same child twice in a row should be avoided, False otherwise.
        """
        return (self["mode"] == 1)

    @avoid_repeats.setter
    def avoid_repeats(self, value: bool) -> None:
        self["mode"] = 1 if value else 0

    @property
    def avoid_repeat_count(self) -> int:
        """Number of recently played children excluded from selection.

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
    def children_ids(self) -> list[int]:
        """Child nodes available for random or sequential playback.

        Returns
        -------
        list[int]
            List of child node hash IDs.
        """
        return self["children/items"]

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

        children: list[int] = self["children/items"]
        if child_id not in children:
            children.append(child_id)
            self["children/count"] = len(children)
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

        children = self["children/items"]
        if child_id in children:
            children.remove(child_id)
            self["children/count"] = len(children)
            return True
        return False

    def clear_children(self) -> None:
        """Disassociates all children from this container."""
        self["children/items"] = []
        self["children/count"] = 0

    @property
    def playlist_ids(self) -> list[int]:
        """Items currently in the playback playlist.

        Returns
        -------
        list[int]
            List of playlist item hash IDs.
        """
        return self["playlist/items"]

    def add_to_playlist(self, item_id: int | Node) -> None:
        """Associates an item with the playback playlist.

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