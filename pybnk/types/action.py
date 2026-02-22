from pybnk import Soundbank, Node
from pybnk.enums import ActionType


class Action(Node):
    """Unified Action node for all action types.

    Actions are triggered by Events and perform operations like playing,
    stopping, pausing sounds, muting buses, or modifying properties.

    Use the appropriate factory method for each action type:
    - Action.new_play() - Start playback
    - Action.new_stop() - Stop playback
    - Action.new_mute_bus() - Mute a bus
    - Action.new_reset_bus_volume() - Reset bus volume
    - Action.new_reset_bus_lpfm() - Reset bus low-pass filter
    """

    # Factory methods for different action types

    @classmethod
    def new_play(
        cls, nid: int, target_id: int, fade_curve: int = 4, bank_id: int = 0
    ) -> "Action":
        """Create a Play action.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_id : int
            Target sound/container ID to play.
        fade_curve : int, default=4
            Fade curve type.
        bank_id : int, default=0
            ID of the target soundbank.

        Returns
        -------
        Action
            New Play action instance.
        """
        temp = cls.load_template(nid, cls.__name__)
        action = cls(temp)

        action.action_type = 1027  # Play action type
        action.target_id = target_id
        action.is_bus = False
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        return action

    @classmethod
    def new_stop(
        cls,
        nid: int,
        target_id: int,
        transition_time: int = 0,
        flags1: int = 4,
        flags2: int = 6,
        bank_id: int = 0,
    ) -> "Action":
        """Create a Stop action.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_id : int
            Target sound/container ID to stop.
        transition_time : int, default=0
            Fade-out time in milliseconds.
        flags1 : int, default=4
            Stop flags 1.
        flags2 : int, default=6
            Stop flags 2.
        bank_id : int, default=0
            ID of the target soundbank.

        Returns
        -------
        Action
            New Stop action instance.
        """
        temp = cls.load_template(nid, cls.__name__)
        action = cls(temp)
        
        action.action_type = 259  # Stop action type
        action.target_id = target_id
        action.is_bus = False
        if transition_time != 0:
            action.transition_time = transition_time
        action["params/StopEO/stop/flags1"] = flags1
        action["params/StopEO/stop/flags2"] = flags2
        action.bank_id = bank_id

        return action

    @classmethod
    def new_mute_bus(
        cls, nid: int, target_bus_id: int, fade_curve: int = 4, bank_id: int = 0,
    ) -> "Action":
        """Create a Mute Bus action.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_bus_id : int
            Target bus ID to mute.
        fade_curve : int, default=4
            Fade curve type.
        bank_id : int, default=0
            ID of the target soundbank.

        Returns
        -------
        Action
            New Mute Bus action instance.
        """
        temp = cls.load_template(nid, cls.__name__)
        action = cls(temp)

        action.action_type = 1538  # Mute bus action type
        action.target_id = target_bus_id
        action.is_bus = True
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        return action

    @classmethod
    def new_reset_bus_volume(
        cls,
        nid: int,
        target_bus_id: int,
        transition_time: int = 2000,
        fade_curve: int = 4,
        bank_id: int = 0,
    ) -> "Action":
        """Create a Reset Bus Volume action.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_bus_id : int
            Target bus ID.
        transition_time : int, default=2000
            Transition time in milliseconds.
        fade_curve : int, default=4
            Fade curve type.
        bank_id : int, default=0
            ID of the target soundbank.

        Returns
        -------
        Action
            New Reset Bus Volume action instance.
        """
        temp = cls.load_template(nid, cls.__name__)
        action = cls(temp)

        action.action_type = 2818  # Reset bus volume action type
        action.target_id = target_bus_id
        action.is_bus = True
        if transition_time != 0:
            action.transition_time = transition_time
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        return action

    @classmethod
    def new_reset_bus_lpfm(
        cls,
        nid: int,
        target_bus_id: int,
        transition_time: int = 2000,
        fade_curve: int = 4,
        bank_id: int = 0,
    ) -> "Action":
        """Create a Reset Bus LPFM (Low-Pass Filter) action.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_bus_id : int
            Target bus ID.
        transition_time : int, default=2000
            Transition time in milliseconds.
        fade_curve : int, default=4
            Fade curve type.
        bank_id : int, default=0
            ID of the target soundbank.

        Returns
        -------
        Action
            New Reset Bus LPFM action instance.
        """
        temp = cls.load_template(nid, cls.__name__)
        action = cls(temp)

        action.action_type = 3842  # Reset bus LPFM action type
        action.target_id = target_bus_id
        action.is_bus = True
        if transition_time != 0:
            action.transition_time = transition_time
        action.fade_curve = fade_curve
        action.bank_id = bank_id
        
        return action

    @property
    def action_type(self) -> ActionType | int:
        """Get the action type identifier.

        Returns
        -------
        int
            Action type code (e.g., 1027=Play, 259=Stop, 1538=Mute).
        """
        return ActionType(self["action_type"])

    @action_type.setter
    def action_type(self, value: ActionType) -> None:
        self["action_type"] = int(value)

    @property
    def target_id(self) -> int:
        """Get the target object ID.

        Returns
        -------
        int
            ID of the target sound/container/bus.
        """
        return self["external_id"]

    @target_id.setter
    def target_id(self, value: int) -> None:
        self["external_id"] = value

    @property
    def is_bus(self) -> bool:
        """Get whether the target is a bus.

        Returns
        -------
        bool
            True if targeting a bus, False if targeting a sound/container.
        """
        return bool(self["is_bus"])

    @is_bus.setter
    def is_bus(self, value: bool) -> None:
        self["is_bus"] = int(value)

    @property
    def transition_time(self) -> int:
        """Get or set the transition time.

        Returns
        -------
        int
            Transition time in milliseconds (0 if not set).
        """
        for prop in self["prop_bundle"]:
            if "TransitionTime" in prop:
                return prop["TransitionTime"]
        return 0

    @transition_time.setter
    def transition_time(self, value: int) -> None:
        # Remove existing TransitionTime if present
        prop_bundle = self["prop_bundle"]
        prop_bundle[:] = [p for p in prop_bundle if "TransitionTime" not in p]
        # Add new value if non-zero
        if value != 0:
            prop_bundle.append({"TransitionTime": value})

    @property
    def fade_curve(self) -> int:
        """Get or set the fade curve (if applicable to this action type).

        Returns
        -------
        int
            Fade curve identifier (0 if not applicable).
        """
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "fade_curve" in params[param_key]:
            return params[param_key]["fade_curve"]
        return 0

    @fade_curve.setter
    def fade_curve(self, value: int) -> None:
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "fade_curve" in params[param_key]:
            params[param_key]["fade_curve"] = value

    @property
    def bank_id(self) -> int:
        """Get  or set the ID of the soundbank this action targets.

        Returns
        -------
        int
            The soundbank's ID.
        """
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "bank_id" in params[param_key]:
            return params[param_key]["bank_id"]
        return 0

    @bank_id.setter
    def bank_id(self, value: int | Soundbank) -> None:
        if isinstance(value, Soundbank):
            value = value.id

        params = self["params"]
        param_key = next(iter(params.keys()))
        if "bank_id" in params[param_key]:
            params[param_key]["bank_id"] = value

    @property
    def exceptions(self) -> list[int]:
        """Get the list of exception IDs (if applicable to this action type).

        Returns
        -------
        list[int]
            List of IDs to exclude from this action.
        """
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "except" in params[param_key]:
            return params[param_key]["except"]["exceptions"]
        return []

    def add_exception(self, exception_id: int) -> None:
        """Add an exception to the action.

        Parameters
        ----------
        exception_id : int
            ID of object to exclude from this action.
        """
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "except" in params[param_key]:
            exceptions = params[param_key]["except"]["exceptions"]
            if exception_id not in exceptions:
                exceptions.append(exception_id)
                params[param_key]["except"]["count"] = len(exceptions)

    def clear_exceptions(self) -> None:
        """Remove all exceptions."""
        params = self["params"]
        param_key = next(iter(params.keys()))
        if "except" in params[param_key]:
            params[param_key]["except"]["exceptions"] = []
            params[param_key]["except"]["count"] = 0
