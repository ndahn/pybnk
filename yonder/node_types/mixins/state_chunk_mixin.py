class StateChunkMixin:
    # TODO build this out a bit more

    @property
    def state_chunk(self) -> dict:
        return self[f"{self.base_params_path}/state_chunk"]

    @property
    def state_property_info(self) -> list[dict]:
        return self.state_chunk["state_property_info"]

    @property
    def state_group_ids(self) -> list[int]:
        return [g["state_group_id"] for g in self.state_chunk["state_group_chunks"]]

    def states(self, state_group_id: int) -> list[tuple[int, int]]:
        for g in self.state_chunk["state_group_chunks"]:
            if g["state_group_id"] == state_group_id:
                return [(x["state_id"], x["state_instance_id"]) for x in g["states"]]

        raise KeyError(f"No state group with ID {state_group_id}")

    def get_references(self) -> list[tuple[str, int]]:
        refs = super().get_references()

        for i, gid in enumerate(self.state_group_ids):
            for j, (_, state_instance_id) in enumerate(self.states(gid)):
                refs.append(
                    (
                        f"{self.base_params_path}/state_chunk/state_group_chunks:{i}/states:{j}/state_instance_id",
                        state_instance_id,
                    )
                )

        return refs
