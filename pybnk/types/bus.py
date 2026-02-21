from pybnk.node import Node


# NOTE not a BaseNode
class Bus(Node):
    """Audio bus for routing and mixing multiple sounds together.
    
    Buses serve as mixing points in the audio hierarchy, allowing shared processing (effects, ducking, HDR) and routing to output devices or parent buses. Supports voice ducking and real-time parameter control.
    """

    @property
    def override_bus_id(self) -> int:
        """Get or set the parent bus ID.
        
        Returns
        -------
        int
            Parent bus ID (0 = master bus).
        """
        return self["initial_values/override_bus_id"]
    
    @override_bus_id.setter
    def override_bus_id(self, value: int) -> None:
        self["initial_values/override_bus_id"] = value

    @property
    def max_instances(self) -> int:
        """Get or set the maximum number of instances.
        
        Returns
        -------
        int
            Maximum instance count (0 = unlimited).
        """
        return self["initial_values/bus_initial_params/max_instance_count"]
    
    @max_instances.setter
    def max_instances(self, value: int) -> None:
        self["initial_values/bus_initial_params/max_instance_count"] = value

    @property
    def channel_config(self) -> int:
        """Get or set the channel configuration.
        
        Returns
        -------
        int
            Channel configuration value.
        """
        return self["initial_values/bus_initial_params/channel_config"]
    
    @channel_config.setter
    def channel_config(self, value: int) -> None:
        self["initial_values/bus_initial_params/channel_config"] = value

    @property
    def recovery_time(self) -> int:
        """Get or set the ducking recovery time in milliseconds.
        
        Returns
        -------
        int
            Recovery time in ms after ducking ends.
        """
        return self["initial_values/recovery_time"]
    
    @recovery_time.setter
    def recovery_time(self, value: int) -> None:
        self["initial_values/recovery_time"] = value

    @property
    def max_duck_volume(self) -> float:
        """Get or set the maximum duck volume in dB.
        
        Returns
        -------
        float
            Maximum duck volume attenuation.
        """
        return self["initial_values/max_duck_volume"]
    
    @max_duck_volume.setter
    def max_duck_volume(self, value: float) -> None:
        self["initial_values/max_duck_volume"] = value

    @property
    def ducks(self) -> list[dict]:
        """Get the list of ducking configurations.
        
        Returns
        -------
        list[dict]
            List of duck dictionaries with target bus and fade times.
        """
        return self["initial_values/ducks"]
    
    @property
    def duck_count(self) -> int:
        """Get the number of ducking configurations.
        
        Returns
        -------
        int
            Number of ducks.
        """
        return self["initial_values/duck_count"]

    @property
    def rtpcs(self) -> list[dict]:
        """Get the RTPC (real-time parameter control) entries.
        
        Returns
        -------
        list[dict]
            List of RTPC dictionaries.
        """
        return self["initial_values/initial_rtpc/rtpcs"]
    
    @property
    def rtpc_count(self) -> int:
        """Get the number of RTPC entries.
        
        Returns
        -------
        int
            Number of RTPCs.
        """
        return self["initial_values/initial_rtpc/count"]

    def add_duck(self, target_bus_id: int, duck_volume: float = -200.0,
                 fade_out: int = 3000, fade_in: int = 500, 
                 fade_curve: str = "SCurve") -> None:
        """Add a ducking configuration for another bus.
        
        Parameters
        ----------
        target_bus_id : int
            Bus ID to duck when this bus plays.
        duck_volume : float, default=-200.0
            Volume to duck to in dB.
        fade_out : int, default=3000
            Fade out time in milliseconds.
        fade_in : int, default=500
            Fade in time in milliseconds.
        fade_curve : str, default="SCurve"
            Fade curve type.
        """
        duck = {
            "bus_id": target_bus_id,
            "duck_volume": duck_volume,
            "fade_out_time": fade_out,
            "fade_in_time": fade_in,
            "fade_curve": fade_curve,
            "target_prop": "BusVolume"
        }
        self["initial_values/ducks"].append(duck)
        self["initial_values/duck_count"] = len(self["initial_values/ducks"])
    
    def remove_duck(self, target_bus_id: int) -> bool:
        """Remove a ducking configuration by target bus ID.
        
        Parameters
        ----------
        target_bus_id : int
            Target bus ID to remove ducking for.
            
        Returns
        -------
        bool
            True if duck was removed, False if not found.
        """
        ducks = self["initial_values/ducks"]
        for i, duck in enumerate(ducks):
            if duck["bus_id"] == target_bus_id:
                ducks.pop(i)
                self["initial_values/duck_count"] = len(ducks)
                return True
        return False
    
    def clear_ducks(self) -> None:
        """Remove all ducking configurations."""
        self["initial_values/ducks"] = []
        self["initial_values/duck_count"] = 0
    
    def clear_rtpcs(self) -> None:
        """Remove all RTPC entries."""
        self["initial_values/initial_rtpc/rtpcs"] = []
        self["initial_values/initial_rtpc/count"] = 0

    def get_aux_bus(self, index: int) -> int:
        """Get an auxiliary bus ID by index.
        
        Parameters
        ----------
        index : int
            Aux bus index (1-4).
            
        Returns
        -------
        int
            Aux bus ID.
        """
        if index < 1 or index > 4:
            raise ValueError("Aux index must be between 1 and 4")
        return self[f"initial_values/bus_initial_params/aux_params/aux{index}"]
    
    def set_aux_bus(self, index: int, bus_id: int) -> None:
        """Set an auxiliary bus ID by index.
        
        Parameters
        ----------
        index : int
            Aux bus index (1-4).
        bus_id : int
            Aux bus ID to set.
        """
        if index < 1 or index > 4:
            raise ValueError("Aux index must be between 1 and 4")
        self[f"initial_values/bus_initial_params/aux_params/aux{index}"] = bus_id