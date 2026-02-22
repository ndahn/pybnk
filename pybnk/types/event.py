from pybnk.node import Node
from pybnk.enums import SoundType


class Event(Node):
    """Event that triggers actions in response to game calls.
    
    Events are the interface between game code and Wwise audio. When the
    game posts an event, it executes the associated actions (play, stop, etc.).
    """

    @classmethod
    def new(cls, name: str) -> "Event":
        """Create a new Event node.
        
        Parameters
        ----------
        name : str
            The name by which this event will be triggered, e.g. "Play_c123456789".
            
        Returns
        -------
        Event
            New Event instance.
        """
        temp = cls.load_template(cls.__name__)

        event = cls(temp)
        event.id = name

        return event

    @classmethod
    def make_event_name(sound_type: SoundType, event_id: int, event_type: str = None) -> str:
        if not 0 < event_id < 1_000_000_000:
            raise ValueError(f"event ID {event_id} outside expected range")

        if not event_type:
            return f"{sound_type}{event_id:010d}"

        return f"{event_type}_{sound_type}{event_id:010d}"

    @property
    def actions(self) -> list[int]:
        """Get the list of action IDs.
        
        Returns
        -------
        list[int]
            List of action node IDs.
        """
        return self["actions"]
    
    @property
    def action_count(self) -> int:
        """Get the number of actions.
        
        Returns
        -------
        int
            Number of actions.
        """
        return self["action_count"]
    
    def add_action(self, action_id: int | Node) -> None:
        """Add an action to the event.
        
        Parameters
        ----------
        action_id : int | Node
            Action node ID or Action instance.
        """
        if isinstance(action_id, Node):
            action_id = action_id.id
        
        actions = self["actions"]
        if action_id not in actions:
            actions.append(action_id)
            self["action_count"] = len(actions)
    
    def remove_action(self, action_id: int | Node) -> bool:
        """Remove an action from the event.
        
        Parameters
        ----------
        action_id : int | Node
            Action node ID or Action instance to remove.
            
        Returns
        -------
        bool
            True if action was removed, False if not found.
        """
        if isinstance(action_id, Node):
            action_id = action_id.id
        
        actions = self["actions"]
        if action_id in actions:
            actions.remove(action_id)
            self["action_count"] = len(actions)
            return True
        return False
    
    def clear_actions(self) -> None:
        """Remove all actions from the event."""
        self["actions"] = []
        self["action_count"] = 0