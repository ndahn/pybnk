from typing import Any
from pathlib import Path
from dataclasses import dataclass
import json

from pybnk.common.util import calc_hash
from pybnk.common.attributes import get_id, get_body


@dataclass
class Soundbank:
    bnk_dir: Path
    json: dict
    id: int
    hirc: list[dict]
    id2index: dict[int, int]  # ID (or hash) to HIRC index

    def update_json(self) -> None:
        """Update this soundbank's json with its current HIRC."""
        sections = self.json["sections"]
        for sec in sections:
            if "HIRC" in sec["body"]:
                sec["body"]["HIRC"]["objects"] = self.hirc
                break

    def __getitem__(self, key: int) -> dict:
        idx = self.id2index[key]
        return self.hirc[idx]

def load_soundbank(bnk_dir: str) -> Soundbank:
    """Load a soundbank and return a more manageable representation."""
    # Resolve the path to the unpacked soundbank
    bnk_dir: Path = Path(bnk_dir)
    if not bnk_dir.is_absolute():
        bnk_dir = Path(__file__).resolve().parent / bnk_dir
    
    bnk_dir = bnk_dir.resolve()

    json_path = bnk_dir / "soundbank.json"
    with json_path.open() as f:
        bnk_json: dict = json.load(f)

    # Read the sections
    sections = bnk_json.get("sections", None)

    if not sections:
        raise ValueError("Could not find 'sections' in bnk")

    for sec in sections:
        body = sec["body"]

        if "BKHD" in body:
            bnk_id = body["BKHD"]["bank_id"]
        elif "HIRC" in body:
            hirc: list[dict] = body["HIRC"]["objects"]
        else:
            pass

    # A helper dict for mapping object IDs to HIRC indices
    id2index = {}
    for idx, obj in enumerate(hirc):
        idsec = obj["id"]
        if "Hash" in idsec:
            oid = idsec["Hash"]
            id2index[oid] = idx
        elif "String" in idsec:
            eid = idsec["String"]
            id2index[eid] = idx
            # Events are sometimes referred to by their hash, but it's not included in the json
            oid = calc_hash(eid)
            id2index[oid] = idx
        else:
            print(f"Don't know how to handle object with id {idsec}")

    return Soundbank(bnk_dir, bnk_json, bnk_id, hirc, id2index)


def verify_soundbank(bnk: Soundbank, required_ids: list[int] = None) -> list[str]:
    discovered_ids = set([0])
    issues = []

    required_ids: set = set(required_ids or [])
    verified_ids = set()

    # We check absolutely everything!
    def delve(item: dict | list | Any, node_id: int, path: str):
        if isinstance(item, list):
            for idx, value in enumerate(item):
                delve(value, node_id, path + f"[{idx}]")

        elif isinstance(item, dict):
            for key, value in item.items():
                delve(value, node_id, path + "/" + key)

        # There's like one 5-digit hash (possibly empty string?), all others are above 10 mio
        elif isinstance(item, int) and item >= 1000000:
            if path.endswith("source_id"):
                # WEMs won't appear in the HIRC
                pass

            elif path.endswith("bank_id"):
                if item != bnk.id:
                    # Not sure if this can be an issue
                    issues.append(f"{node_id}:reference to external soundbank {item}")
            
            elif path.endswith("id/Hash"):
                if item in discovered_ids:
                    issues.append(f"{node_id}: has duplicates")

            elif path.endswith("id/String"):
                if calc_hash(item) in discovered_ids:
                    issues.append(f"{node_id}: has duplicates")
            
            elif path.endswith("direct_parent_id"):
                if item in discovered_ids:
                    issues.append(f"{node_id}: is defined after its parent {item}")

            elif item not in discovered_ids:
                issues.append(f"{node_id}: {path}: reference {item} does not exist (probably okay?)")

    for node in bnk.hirc:
        node_id = get_id(node)

        if node_id in discovered_ids:
            issues.append(f"{node_id}: node has been defined before")
            continue

        discovered_ids.add(node_id)
        if node_id not in required_ids:
            continue

        delve(get_body(node), node_id, "")

        # References to other objects will always be by hash
        if isinstance(node_id, str):
            node_id = calc_hash(node_id)

        verified_ids.add(node_id)

    if required_ids and len(verified_ids) < len(required_ids):
        issues.append(f"Expected nodes not found: {[required_ids.difference(verified_ids)]}")

    return issues
