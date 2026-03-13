from yonder.util import logger


class PropertiesMixin:
    @property
    def properties(self) -> dict[str, float]:
        """Initial property values.

        Returns
        -------
        dict[str, float]
            Dict of property initial values.
        """
        node_properties = self[f"{self.base_params_path}/node_initial_params/prop_initial_values"]
        # Much easier to manage
        properties = {}

        for d in node_properties:
            if len(d) != 1:
                logger.error(f"Don't know how to handle property {d}")
                continue

            key = next(k for k in d.keys())
            properties[key] = d[key]

        return properties

    def get_property(self, prop_name: str, default: float = None) -> float:
        """Get a property value by name.

        Parameters
        ----------
        prop_name : str
            Property name (e.g., 'Volume', 'Pitch', 'LPF', 'HPF').
        default : float, optional
            Default value if property not found.

        Returns
        -------
        float
            Property value, or default if not found.
        """
        return self.properties.get(prop_name, default)

    def set_property(self, prop_name: str, value: float) -> None:
        """Set a property value by name.

        If the property already exists, updates it. Otherwise, adds it.

        Parameters
        ----------
        prop_name : str
            Property name (e.g., 'Volume', 'Pitch', 'LPF', 'HPF').
        value : float
            Property value to set.
        """
        # Try to find and update existing property
        node_properties = self[f"{self.base_params_path}/node_initial_params/prop_initial_values"]
        for prop_dict in node_properties:
            if prop_name in prop_dict:
                prop_dict[prop_name] = value
                return

        # Property doesn't exist, add it
        node_properties.append({prop_name: value})

    def remove_property(self, prop_name: str) -> bool:
        """Remove a property by name.

        Parameters
        ----------
        prop_name : str
            Property name to remove.

        Returns
        -------
        bool
            True if property was removed, False if not found.
        """
        prop_values = self[f"{self.base_params_path}/node_initial_params/prop_initial_values"]
        for i, prop_dict in enumerate(prop_values):
            if prop_name in prop_dict:
                prop_values.pop(i)
                return True
        return False

    def clear_properties(self) -> None:
        """Remove all initial property values."""
        self[f"{self.base_params_path}/node_initial_params/prop_initial_values"] = []

    def get_references(self) -> list[tuple[str, int]]:
        refs = super().get_references()

        for i, (key, val) in enumerate(self.properties.items()):
            if key == "AttenuationID":
                refs.append(
                    (
                        f"{self.base_params_path}/node_initial_params/prop_initial_values:{i}/"
                        "AttenuationID",
                        int(val),
                    )
                )

        return refs
