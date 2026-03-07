from typing import Any
from pathlib import Path

from pybnk.util import resource_data


_lookup_table: dict[int, str] = {}


def calc_hash(input: str) -> int:
    # This is the FNV-1a 32-bit hash taken from rewwise
    # https://github.com/vswarte/rewwise/blob/127d665ab5393fb7b58f1cade8e13a46f71e3972/analysis/src/fnv.rs#L6
    FNV_BASE = 2166136261
    FNV_PRIME = 16777619

    input_bytes = input.lower().encode()

    result = FNV_BASE
    for byte in input_bytes:
        result *= FNV_PRIME
        # Ensure it stays within 32-bit range
        result &= 0xFFFFFFFF
        result ^= byte

    return result


def load_lookup_table(path: Path = None) -> dict[int, str]:
    if not path:
        pairs = resource_data("wwise_ids.txt").splitlines()
    else:
        pairs = [x.strip() for x in path.read_text().splitlines()]

    table = {}
    for x in pairs:
        if x.startswith("#"):
            continue

        h = calc_hash(x)
        table[h] = x.strip(" \n")

    return table


def get_name_for_hash(h: int, default: Any = None) -> str:
    global _lookup_table

    if not _lookup_table:
        _lookup_table = load_lookup_table()
    
    return _lookup_table.get(h, default)
