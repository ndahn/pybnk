import os
from pathlib import Path
import shutil

from pybnk import Soundbank


def import_wems(bnk: Soundbank, wems: list[Path]) -> None:
    for wem in wems:
        if not wem.endswith(".wem"):
            continue

        # We allow adding a prefix to the wem ID to make them easier to handle
        if "_" in wem.name:
            _, wem_id = wem.stem.rsplit("_", maxsplit=1)
            wem_id = int(wem_id)
        else:
            wem_id = int(wem.stem)

        target_path = bnk.bnk_dir / f"{wem_id}.wem"
        shutil.copy(wem, target_path)

        sound_nodes = list(bnk.query({
            "type": "Sound",
            "bank_source_data/media_information/source_id": wem_id,
        }))

        wem_size = os.path.getsize(str(target_path))
        for node in sound_nodes:
            node["bank_source_data/media_information/in_memory_media_size"] = wem_size


# TODO add helper for making prefetch snippets
