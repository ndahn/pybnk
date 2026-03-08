from pybnk import Node
from pybnk.util import logger, PathDict
from .wwise_node import WwiseNode


class MusicSwitchContainer(WwiseNode):
    """Specialized node for MusicSwitchContainer type.

    Music switch containers select which music segment to play based on game
    state using a decision tree. Supports complex transition rules between
    segments and multi-dimensional state-based selection.
    """

    @classmethod
    def new(
        cls,
        nid: int,
        tempo: float = 120.0,
        time_signature: tuple[int, int] = (4, 4),
        parent_id: int = 0,
    ) -> "MusicSwitchContainer":
        """Create a new MusicSwitchContainer node.

        Parameters
        ----------
        nid : int
            Node ID (hash).
        tempo : float, default=120.0
            Tempo in BPM.
        time_signature : tuple[int, int], default=(4, 4)
            Time signature (beat_count, beat_value).
        parent_id : int, default=0
            Parent node ID.

        Returns
        -------
        MusicSwitchContainer
            New MusicSwitchContainer instance.
        """
        node = cls.from_template(nid, "MusicSwitchContainer")
        container = cls(node.dict)
        container.tempo = tempo
        container.time_signature = time_signature
        if parent_id != 0:
            container.parent = parent_id
        return container

    @property
    def base_params(self) -> PathDict:
        return PathDict(
            self["music_trans_node_params/music_node_params/node_base_params"]
        )

    @property
    def music_params(self) -> PathDict:
        return PathDict(self["music_trans_node_params/music_node_params"])

    @property
    def tempo(self) -> float:
        """Get or set the tempo in BPM.

        Returns
        -------
        float
            Tempo in beats per minute.
        """
        self.music_params["meter_info/tempo"]

    @tempo.setter
    def tempo(self, value: float) -> None:
        self.music_params["meter_info/tempo"] = value

    @property
    def time_signature(self) -> tuple[int, int]:
        """Get or set the time signature.

        Returns
        -------
        tuple[int, int]
            (beat_count, beat_value) e.g., (4, 4) for 4/4 time.
        """
        beat_count = self.music_params["meter_info/time_signature_beat_count"]
        beat_value = self.music_params["meter_info/time_signature_beat_value"]
        return (beat_count, beat_value)

    @time_signature.setter
    def time_signature(self, value: tuple[int, int]) -> None:
        beat_count, beat_value = value
        self.music_params["meter_info/time_signature_beat_count"] = beat_count
        self.music_params["meter_info/time_signature_beat_value"] = beat_value

    @property
    def grid_period(self) -> float:
        """Get or set the grid period in milliseconds.

        Returns
        -------
        float
            Grid period in ms.
        """
        self.music_params["meter_info/grid_period"]

    @grid_period.setter
    def grid_period(self, value: float) -> None:
        self.music_params["meter_info/grid_period"] = value

    @property
    def continue_playback(self) -> bool:
        """Get or set whether to continue playback across switches.

        Returns
        -------
        bool
            True if playback continues across switches.
        """
        return bool(self["continue_playback"])

    @continue_playback.setter
    def continue_playback(self, value: bool) -> None:
        self["continue_playback"] = int(value)

    @property
    def tree_depth(self) -> int:
        """Get or set the decision tree depth.

        Returns
        -------
        int
            Tree depth (number of state dimensions).
        """
        return self["tree_depth"]

    @property
    def tree_mode(self) -> str:
        """Get or set the tree mode.

        Returns
        -------
        str
            Tree mode (e.g., 'BestMatch', 'Sequential').
        """
        return self["tree_mode"]

    @tree_mode.setter
    def tree_mode(self, value: str) -> None:
        self["tree_mode"] = value

    @property
    def arguments(self) -> list[int]:
        """Get the list of state group arguments.

        Returns
        -------
        list[int]
            List of group_id arguments.
        """
        args = []
        for a in self["arguments"]:
            gid = a.get("group_id")
            if gid is None:
                logger.warning(f"Found unknown argument {a} in {self}")
            else:
                args.append(gid)
        return args

    @property
    def group_types(self) -> list[str]:
        """Get the list of group types.

        Returns
        -------
        list[str]
            List of group types (typically 'State').
        """
        return self["group_types"]

    @property
    def decision_tree(self) -> dict:
        """Get the decision tree root.

        Returns
        -------
        dict
            Decision tree structure.
        """
        return self["tree"]

    @property
    def transition_rules(self) -> list[dict]:
        """Get the transition rules.

        Returns
        -------
        list[dict]
            List of transition rule dictionaries.
        """
        return self["music_trans_node_params/transition_rules"]

    @property
    def children_ids(self) -> list[int]:
        """Get list of child segment IDs.

        Returns
        -------
        list[int]
            List of child segment hash IDs.
        """
        self.music_params["children/items"]

    def add_argument(self, group_id: int, group_type: str = "State") -> None:
        """Add a state group argument dimension.

        Parameters
        ----------
        group_id : int
            State group ID.
        group_type : str, default="State"
            Group type.
        """
        self["arguments"].append({"group_id": group_id})
        self["group_types"].append(group_type)
        self["tree_depth"] = len(self["arguments"])

    def set_decision_tree(self, tree_dict: dict) -> None:
        """Set the decision tree structure.

        This will flatten the tree and calculate correct first_child_index values
        for serialization to Wwise soundbanks.

        Parameters
        ----------
        tree_dict : dict
            Complete tree structure with keys, node_ids, and children.
        """

        # Flatten the tree and calculate indices
        def _flatten_tree_preorder(node: dict, flattened: list) -> None:
            # Record this node's index and info
            current_index = len(flattened)
            children = node.get("children", [])

            node_info = {
                "index": current_index,
                "key": node.get("key", 0),
                "node_id": node.get("node_id", 0),
                "first_child_index": len(flattened) + 1 if children else 0,
                "child_count": len(children),
                "weight": node.get("weight", 50),
                "probability": node.get("probability", 100),
                "children_indices": [],
            }

            flattened.append(node_info)

            # Process children in order
            for child in children:
                child_index = len(flattened)
                node_info["children_indices"].append(child_index)
                _flatten_tree_preorder(child, flattened)

        flattened = []
        _flatten_tree_preorder(tree_dict, flattened)

        # The root node needs the nested children for the JSON structure
        # but the flattened array has the correct indices
        root_with_children = self._rebuild_nested_structure(flattened)

        self["tree"] = root_with_children
        self["tree_size"] = len(flattened)

        self._rebuild_tree_indices()
        self._update_children_list()

    def add_branch(self, path: tuple[int], node_id: int | Node) -> None:
        if len(path) != len(self.arguments):
            raise ValueError("Path length must be equal to number of tree arguments")

        parent: dict = self.decision_tree
        offset = 0
        for i, key in enumerate(path):
            for child in parent["children"]:
                if child["key"] == key:
                    # Continue searching the child
                    parent = child
                    break
            else:
                # No matching child, we found our parent
                offset = i
                break
        else:
            # For every key we found a matching child, so this path already exists
            raise ValueError(f"Path already exists {path}")

        for key in path[offset:]:
            branch = {
                "key": key,
                "node_id": 0,
                "first_child_index": 0,
                "child_count": 0,
                "weight": 50,
                "probability": 100,
                "children": [],
            }

            # Children MUST be sorted
            children: list[dict] = parent["children"]
            children.append(branch)
            children.sort(key=lambda x: x["key"])

            parent["child_count"] += 1
            parent = branch

        # Set the node ID on the leaf child
        branch["node_id"] = node_id
        self._rebuild_tree_indices()
        self._update_children_list()

    def add_transition_rule(
        self,
        source_ids: list[int],
        destination_ids: list[int],
        source_transition_time: int = 0,
        destination_fade_offset: int = 0,
        source_fade_curve: str = "Linear",
        sync_type: str = "Immediate",
    ) -> None:
        """Add a transition rule between segments.

        Parameters
        ----------
        source_ids : list[int]
            Source segment IDs (-1 = any).
        destination_ids : list[int]
            Destination segment IDs (-1 = any).
        source_transition_time : int, default=0
            Source fade out time in ms.
        destination_fade_offset : int, default=0
            Destination fade offset in ms.
        source_fade_curve : str, default="Linear"
            Fade curve type.
        sync_type : str, default="Immediate"
            Sync type ('Immediate', 'ExitMarker', etc.).
        """
        rule = {
            "source_transition_rule_count": len(source_ids),
            "source_ids": source_ids,
            "destination_transition_rule_count": len(destination_ids),
            "destination_ids": destination_ids,
            "source_transition_rule": {
                "transition_time": source_transition_time,
                "fade_curve": source_fade_curve,
                "fade_offet": 0,
                "sync_type": sync_type,
                "clue_filter_hash": 0,
                "play_post_exit": 0,
            },
            "destination_transition_rule": {
                "transition_time": 0,
                "fade_curve": "Linear",
                "fade_offet": destination_fade_offset,
                "clue_filter_hash": 0,
                "jump_to_id": 0,
                "jump_to_type": 0,
                "entry_type": 0,
                "play_pre_entry": 0,
                "destination_match_source_cue_name": 0,
            },
            "alloc_trans_object_flag": 0,
            "transition_object": {
                "segment_id": 0,
                "fade_out": {"transition_time": 0, "curve": "Log3", "offset": 0},
                "fade_in": {"transition_time": 0, "curve": "Log3", "offset": 0},
                "play_pre_entry": 0,
                "play_post_exit": 0,
            },
        }
        self["music_trans_node_params/transition_rules"].append(rule)
        self["music_trans_node_params/transition_rule_count"] = len(
            self["music_trans_node_params/transition_rules"]
        )

        self._update_children_list()

    def get_references(self) -> list[tuple[str, int]]:
        paths = (
            "music_trans_node_params/music_node_params/node_base_params/override_bus_id",
            "music_trans_node_params/music_node_params/node_base_params/aux_params/aux1",
            "music_trans_node_params/music_node_params/node_base_params/aux_params/aux2",
            "music_trans_node_params/music_node_params/node_base_params/aux_params/aux3",
            "music_trans_node_params/music_node_params/node_base_params/aux_params/aux4",
        )
        refs = [(p, r) for p in paths if (r := self.get(p, 0)) > 0]

        children = self["music_trans_node_params/music_node_params/children/items"]
        for i, child_id in enumerate(children):
            refs.append(
                (
                    f"music_trans_node_params/music_node_params/children/items:{i}",
                    child_id,
                )
            )

        return refs

    def _rebuild_tree_indices(self) -> list[dict]:
        """Recalculate the first_child_index attributes for tree nodes, which represents 
        their indices within a flattened list representation."""
        def delve(tree_node: dict, flattened: list) -> None:
            children = tree_node["children"]
            tree_node["first_child_index"] = len(flattened) + 1 if children else 0
            flattened.append(tree_node)

            for child in children:
                delve(child, flattened)
            
        flat = []
        delve(self.decision_tree, flat)
        return flat

    def _update_children_list(self) -> None:
        """Update children list from all sources.

        Collects segment IDs from:
        1. Tree leaf nodes
        2. Transition rule source_ids
        3. Transition rule destination_ids
        4. Transition object segment_id

        Ensures children are unique and sorted ascending.
        """
        children_set = set()

        def _collect_from_tree(node: dict, children_set: set) -> None:
            node_id = node.get("node_id", 0)
            if node_id > 0:
                children_set.add(node_id)

            for child in node.get("children", []):
                _collect_from_tree(child, children_set)

        _collect_from_tree(self["tree"], children_set)

        # Collect from transition rules
        for rule in self["music_trans_node_params/transition_rules"]:
            # Source IDs
            for sid in rule.get("source_ids", []):
                if sid > 0:
                    children_set.add(sid)

            # Destination IDs
            for did in rule.get("destination_ids", []):
                if did > 0:
                    children_set.add(did)

            # Transition object segment_id
            trans_obj = rule.get("transition_object", {})
            segment_id = trans_obj.get("segment_id", 0)
            if segment_id > 0:
                children_set.add(segment_id)

        # Update the children list
        children = self.music_params["children/items"]
        children.clear()
        children.extend(sorted(c for c in children_set if c > 0))
        self.music_params["children/count"] = len(children)
