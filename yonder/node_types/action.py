from typing import Any
from yonder import Soundbank, Node
from yonder.enums import ActionType
from yonder.util import logger


class Action(Node):
    """Unified Action node for all action types.

    Actions are triggered by Events and perform operations like playing, stopping, pausing sounds, muting buses, or modifying properties.
    """

    # Factory methods for different action types

    @classmethod
    def new_play_action(
        cls, nid: int, target_id: int, fade_curve: int = 4, bank_id: int = 0
    ) -> "Action":
        """Creates an action that starts audio playback.

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
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 1027  # Play action type
        action.set("params/Play", {})
        action.target_id = target_id
        action.is_bus = False
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        logger.info(f"Created new node {action}")
        return action

    @classmethod
    def new_event_action(
        cls, nid: int, target_event_id: int, delay: int = 0
    ) -> "Action":
        """Creates an action that triggers another event.

        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_event_id : int
            ID of the event to trigger.
        delay : int, default=0
            Delay after which to trigger the event

        Returns
        -------
        Action
            New PlayEvent action instance.
        """
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 8451
        action.target_id = target_event_id
        action.set("params", "PlayEvent")
        if delay > 0:
            action.delay = delay

        logger.info(f"Created new node {action}")
        return action

    @classmethod
    def new_stop_action(
        cls,
        nid: int,
        target_id: int,
        transition_time: int = 0,
        flags1: int = 4,
        flags2: int = 6,
        bank_id: int = 0,
    ) -> "Action":
        """Creates an action that stops audio playback.

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
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 259  # Stop action type
        action.set(
            "params/StopEO",
            {
                "params/StopEO/stop/flags1": flags1,
                "params/StopEO/stop/flags2": flags2,
            },
            create=True,
        )

        action.target_id = target_id
        action.is_bus = False
        if transition_time != 0:
            action.transition_time = transition_time
        action.bank_id = bank_id

        logger.info(f"Created new node {action}")
        return action

    @classmethod
    def new_set_state_action(
        cls,
        nid: int,
        switch_group_id: int,
        switch_state_id: int,
    ) -> "Action":
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 4612  # Set state action type
        action.set(
            "params/SetState",
            {
                "params/SetState/switch_group_id",
                switch_group_id,
                "params/SetState/switch_state_id",
                switch_state_id,
            },
        )

        logger.info(f"Created new node {action}")
        return action

    @classmethod
    def new_mute_bus_action(
        cls,
        nid: int,
        target_bus_id: int,
        fade_curve: int = 4,
        bank_id: int = 0,
    ) -> "Action":
        """Creates an action that mutes a bus, silencing all audio routed through it.

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
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 1538  # Mute bus action type
        action.set("params/MuteM", {})
        action.target_id = target_bus_id
        action.is_bus = True
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        logger.info(f"Created new node {action}")
        return action

    # TODO SetVolumeM action 2562
    # TODO ResetVolumeM action 2818
    # TODO UnmuteM (bus) action 1794
    # TODO UnmuteALL (bus) action 1796
    # TODO ResetBusVolumeALL action 3332

    @classmethod
    def new_reset_bus_volume_action(
        cls,
        nid: int,
        target_bus_id: int,
        transition_time: int = 2000,
        fade_curve: int = 4,
        bank_id: int = 0,
    ) -> "Action":
        """Creates an action that restores a bus to its default volume.

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
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 3330  # Reset bus volume action type
        action.set("params/ResetBusVolumeM", {})

        action.target_id = target_bus_id
        action.is_bus = True
        if transition_time != 0:
            action.transition_time = transition_time
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        logger.info(f"Created new node {action}")
        return action

    @classmethod
    def new_reset_bus_lpfm_action(
        cls,
        nid: int,
        target_bus_id: int,
        transition_time: int = 2000,
        fade_curve: int = 4,
        bank_id: int = 0,
    ) -> "Action":
        """Creates an action that restores a bus's low-pass filter to default settings.

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
        temp = cls.load_template(cls.__name__)
        action = cls(temp)

        action.id = nid
        action.action_type = 3842  # Reset bus LPFM action type
        action.target_id = target_bus_id
        action.is_bus = True
        if transition_time != 0:
            action.transition_time = transition_time
        action.fade_curve = fade_curve
        action.bank_id = bank_id

        logger.info(f"Created new node {action}")
        return action

    @property
    def action_type(self) -> ActionType | int:
        """Action type identifier.

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
        """Target object ID.

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
        """Indicates whether this action targets a bus or a sound/container.

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
        """Transition time.

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
    def delay(self) -> int:
        """Delay before this action activates.

        Returns
        -------
        int
            Delay in milliseconds (0 if not set).
        """
        for prop in self["prop_bundle"]:
            if "Delay" in prop:
                return prop["Delay"]
        return 0

    @delay.setter
    def delay(self, value: int) -> None:
        # Remove existing delay if present
        prop_bundle = self["prop_bundle"]
        prop_bundle[:] = [p for p in prop_bundle if "Delay" not in p]
        # Add new value if non-zero
        if value != 0:
            prop_bundle.append({"Delay": value})

    @property
    def params(self) -> dict[str, Any]:
        params = self["params"]
        if isinstance(params, str):
            # For reference actions like "PlayEvent"
            return {params: {}}

        param_key = next(iter(params.keys()))
        return params[param_key]

    @property
    def fade_curve(self) -> int:
        """Fade curve (if applicable to this action type).

        Returns
        -------
        int
            Fade curve identifier (0 if not applicable).
        """
        params = self.params
        if "fade_curve" in params:
            return params["fade_curve"]
        return 0

    @fade_curve.setter
    def fade_curve(self, value: int) -> None:
        self.params["fade_curve"] = value

    @property
    def bank_id(self) -> int:
        """Soundbank containing the target of this action.

        Returns
        -------
        int
            The soundbank's ID.
        """
        return self.params.get("bank_id", 0)

    @bank_id.setter
    def bank_id(self, value: int | Soundbank) -> None:
        if isinstance(value, Soundbank):
            value = value.id

        self.params["bank_id"] = value

    @property
    def exceptions(self) -> list[int]:
        """Objects excluded from this action's effects.

        Returns
        -------
        list[int]
            List of IDs to exclude from this action.
        """
        params = self.params
        if "except" in params:
            return params["except"]["exceptions"]
        return []

    def add_exception(self, exception_id: int) -> None:
        """Excludes a specific object from this action's effects.

        Parameters
        ----------
        exception_id : int
            ID of object to exclude from this action.
        """
        params = self.params
        if "except" in params:
            exceptions = params["except"]["exceptions"]
            if exception_id not in exceptions:
                exceptions.append(exception_id)
                params["except"]["count"] = len(exceptions)

    def clear_exceptions(self) -> None:
        """Clears all exceptions, allowing this action to affect all targets."""
        params = self.params
        if "except" in params:
            params["except"]["exceptions"] = []
            params["except"]["count"] = 0

    def get_references(self) -> list[tuple[str, int]]:
        return super().get_references() + [("external_id", self.target_id)]
