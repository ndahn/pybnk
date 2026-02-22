from node import Node


class Action(Node):
    """Base class for Action nodes that perform operations on audio objects.
    
    Actions are triggered by Events and perform operations like playing,
    stopping, pausing sounds, or modifying properties.
    """

    @property
    def action_type(self) -> int:
        """Get the action type identifier.
        
        Returns
        -------
        int
            Action type code.
        """
        return self["action_type"]
    
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


class ActionPlay(Action):
    """Play action that starts playback of a sound or container.
    
    Triggers audio playback when the associated event is posted.
    """

    @classmethod
    def new(cls, nid: int, target_id: int, fade_curve: int = 4,
            bank_id: int = 0) -> "ActionPlay":
        """Create a new Play action.
        
        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_id : int
            Target sound/container ID to play.
        fade_curve : int, default=4
            Fade curve type.
        bank_id : int, default=0
            Bank ID containing the target.
            
        Returns
        -------
        ActionPlay
            New ActionPlay instance.
        """
        node = cls.from_template(nid, "Action_Play")
        action = cls(node.dict)
        action.target_id = target_id
        action.fade_curve = fade_curve
        if bank_id != 0:
            action.bank_id = bank_id
        return action

    @property
    def fade_curve(self) -> int:
        """Get or set the fade curve type.
        
        Returns
        -------
        int
            Fade curve identifier.
        """
        return self["params/Play/fade_curve"]
    
    @fade_curve.setter
    def fade_curve(self, value: int) -> None:
        self["params/Play/fade_curve"] = value

    @property
    def bank_id(self) -> int:
        """Get or set the bank ID.
        
        Returns
        -------
        int
            Bank ID.
        """
        return self["params/Play/bank_id"]
    
    @bank_id.setter
    def bank_id(self, value: int) -> None:
        self["params/Play/bank_id"] = value


class ActionStop(Action):
    """Stop action that halts playback of a sound or container.
    
    Stops audio playback when the associated event is posted, with
    optional fade-out and exception handling.
    """

    @classmethod
    def new(cls, nid: int, target_id: int, transition_time: int = 0,
            flags1: int = 5, flags2: int = 6) -> "ActionStop":
        """Create a new Stop action.
        
        Parameters
        ----------
        nid : int
            Action ID (hash).
        target_id : int
            Target sound/container ID to stop.
        transition_time : int, default=0
            Fade-out time in milliseconds.
        flags1 : int, default=5
            Stop flags 1.
        flags2 : int, default=6
            Stop flags 2.
            
        Returns
        -------
        ActionStop
            New ActionStop instance.
        """
        node = cls.from_template(nid, "Action_Stop")
        action = cls(node.dict)
        action.target_id = target_id
        if transition_time != 0:
            action.transition_time = transition_time
        action.stop_flags1 = flags1
        action.stop_flags2 = flags2
        return action

    @property
    def transition_time(self) -> int:
        """Get or set the transition (fade-out) time.
        
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
    def stop_flags1(self) -> int:
        """Get or set stop flags 1.
        
        Returns
        -------
        int
            Stop flags 1.
        """
        return self["params/StopEO/stop/flags1"]
    
    @stop_flags1.setter
    def stop_flags1(self, value: int) -> None:
        self["params/StopEO/stop/flags1"] = value

    @property
    def stop_flags2(self) -> int:
        """Get or set stop flags 2.
        
        Returns
        -------
        int
            Stop flags 2.
        """
        return self["params/StopEO/stop/flags2"]
    
    @stop_flags2.setter
    def stop_flags2(self, value: int) -> None:
        self["params/StopEO/stop/flags2"] = value

    @property
    def exceptions(self) -> list[int]:
        """Get the list of exception IDs.
        
        Returns
        -------
        list[int]
            List of IDs to exclude from stopping.
        """
        return self["params/StopEO/except/exceptions"]
    
    def add_exception(self, exception_id: int) -> None:
        """Add an exception to the stop action.
        
        Parameters
        ----------
        exception_id : int
            ID of object to exclude from stopping.
        """
        exceptions = self["params/StopEO/except/exceptions"]
        if exception_id not in exceptions:
            exceptions.append(exception_id)
            self["params/StopEO/except/count"] = len(exceptions)
    
    def clear_exceptions(self) -> None:
        """Remove all exceptions."""
        self["params/StopEO/except/exceptions"] = []
        self["params/StopEO/except/count"] = 0