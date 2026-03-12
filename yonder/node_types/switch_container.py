from yonder.util import logger
from .wwise_node import WwiseNode
from .mixins import ContainerMixin


class SwitchContainer(WwiseNode, ContainerMixin):
    """Specialized node for SwitchContainer type.

    Switch containers select which child to play based on game state variables (switches). Each switch value maps to a specific child or set of children, enabling dynamic audio selection based on gameplay conditions.
    """

    @classmethod
    def new(
        cls, nid: int, group_id: int, default_switch: int, parent_id: int = 0
    ) -> "SwitchContainer":
        """Create a new SwitchContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        group_id : int
            Switch group ID.
        default_switch : int
            Default switch value ID.
        parent_id : int, default=0
            Parent node ID.

        Returns
        -------
        SwitchContainer
            New SwitchContainer instance.
        """
        temp = cls.load_template(cls.__name__)

        container = cls(temp)
        container.id = nid
        container.group_id = group_id
        container.default_switch = default_switch
        if parent_id is not None:
            container.parent = parent_id

        logger.info(f"Created new node {container}")
        return container

    @property
    def group_type(self) -> int:
        """Group type.

        Returns
        -------
        int
            Group type identifier.
        """
        return self["group_type"]

    @group_type.setter
    def group_type(self, value: int) -> None:
        self["group_type"] = value

    @property
    def group_id(self) -> int:
        """Switch group ID.

        Returns
        -------
        int
            Switch group ID.
        """
        return self["group_id"]

    @group_id.setter
    def group_id(self, value: int) -> None:
        self["group_id"] = value

    @property
    def default_switch(self) -> int:
        """Default switch.

        Returns
        -------
        int
            Default switch ID.
        """
        return self["default_switch"]

    @default_switch.setter
    def default_switch(self, value: int) -> None:
        self["default_switch"] = value

    @property
    def continuous_validation(self) -> bool:
        """Whether to continuously validate the switches' state.

        Returns
        -------
        bool
            True if continuous validation is enabled.
        """
        return bool(self["continuous_validation"])

    @continuous_validation.setter
    def continuous_validation(self, value: bool) -> None:
        self["continuous_validation"] = int(value)

    @property
    def switch_mappings(self) -> dict[int, list[int]]:
        res = {}
        for g in self.switch_groups:
            res.setdefault(g["switch_id"], []).extend(g["nodes"])
        return res

    @property
    def switch_groups(self) -> list[dict]:
        """Get the list of switch group mappings.

        Returns
        -------
        list[dict]
            List of switch mappings (switch_id -> node list).
        """
        return self["switch_groups"]

    @property
    def switch_params(self) -> list[dict]:
        """Get the list of switch parameters per child.

        Returns
        -------
        list[dict]
            List of switch parameter configurations.
        """
        return self["switch_params"]

    def clear(self) -> None:
        """Remove all children from the container."""
        self["children/items"] = []
        self["children/count"] = 0
        self["switch_groups"] = []
        self["switch_group_count"] = 0
        self["switch_params"] = []
        self["switch_param_count"] = 0

    def _update_children_list(self) -> None:
        children_set = set()
        for param in self.switch_params:
            children_set.add(param.get("node_id", 0))

        for group in self.switch_groups:
            children_set.update(group.get("nodes", []))

        # Update the children list
        children = self.base_params["children/items"]
        children.clear()
        children.extend(sorted(c for c in children_set if c > 0))
        self.base_params["children/count"] = len(children)

    def add_switch_mapping(self, switch_id: int, node_ids: list[int]) -> None:
        """Map a switch value to one or more child nodes.

        Parameters
        ----------
        switch_id : int
            Switch value ID.
        node_ids : list[int]
            List of child node IDs to play for this switch.
        """
        switch_group = {
            "switch_id": switch_id,
            "node_count": len(node_ids),
            "nodes": node_ids,
        }
        self["switch_groups"].append(switch_group)
        self["switch_group_count"] = len(self["switch_groups"])
        self._update_children_list()

    def remove_switch_mapping(self, switch_id: int) -> bool:
        """Remove a switch mapping.

        Parameters
        ----------
        switch_id : int
            Switch value ID to remove.

        Returns
        -------
        bool
            True if mapping was removed, False if not found.
        """
        switch_groups = self["switch_groups"]
        for i, group in enumerate(switch_groups):
            if group["switch_id"] == switch_id:
                switch_groups.pop(i)
                self["switch_group_count"] = len(switch_groups)
                self._update_children_list()
                return True

        return False

    def get_nodes_for_switch(self, switch_id: int) -> list[int]:
        """Get the node IDs assigned to a switch value.

        Parameters
        ----------
        switch_id : int
            Switch value ID.

        Returns
        -------
        list[int]
            List of node IDs for this switch (empty if not found).
        """
        for group in self["switch_groups"]:
            if group["switch_id"] == switch_id:
                return group["nodes"]

        return []

    def add_switch_param(
        self,
        node_id: int,
        fade_out_time: int = 0,
        fade_in_time: int = 0,
        continue_playback: bool = False,
        is_first_only: bool = False,
    ) -> None:
        """Add switch parameters for a child node.

        Parameters
        ----------
        node_id : int
            Child node ID.
        fade_out_time : int, default=0
            Fade out time in milliseconds.
        fade_in_time : int, default=0
            Fade in time in milliseconds.
        continue_playback : bool, default=False
            Whether to continue playback across switches.
        is_first_only : bool, default=False
            Whether to play only the first matching node.
        """
        param = {
            "node_id": node_id,
            "unk1": False,
            "unk2": False,
            "unk3": False,
            "unk4": False,
            "unk5": False,
            "unk6": False,
            "continue_playback": continue_playback,
            "is_first_only": is_first_only,
            "unk9": False,
            "unk10": False,
            "unk11": False,
            "unk12": False,
            "unk13": False,
            "unk14": False,
            "unk15": False,
            "unk16": True,
            "fade_out_time": fade_out_time,
            "fade_in_time": fade_in_time,
        }
        self["switch_params"].append(param)
        self["switch_param_count"] = len(self["switch_params"])
        self._update_children_list()

    def _remove_from_switch_groups(self, node_id: int) -> None:
        """Remove node from all switch group mappings."""
        for group in self["switch_groups"]:
            if node_id in group["nodes"]:
                group["nodes"].remove(node_id)
                group["node_count"] = len(group["nodes"])

        self._update_children_list()

    def _remove_from_switch_params(self, node_id: int) -> None:
        """Remove node from switch params."""
        params = self["switch_params"]
        self["switch_params"] = [p for p in params if p["node_id"] != node_id]
        self["switch_param_count"] = len(self["switch_params"])
        self._update_children_list()
