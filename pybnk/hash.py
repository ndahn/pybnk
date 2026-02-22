from pathlib import Path
from importlib import resources


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
    import pybnk

    if not path:
        path = "resources/wwise_ids.txt"
        keys = resources.files(pybnk).joinpath(path).read_text()
    else:
        keys = [x.strip() for x in path.read_text().splitlines()]

    return {calc_hash(k): k for k in keys if not k.startswith("#")}


lookup_table = load_lookup_table()
