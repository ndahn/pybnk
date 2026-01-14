from pathlib import Path
from importlib import resources
import subprocess
import shutil
from tkinter import filedialog


_rewwise_exe: Path = None


def get_rewwise_path() -> str:
    global _rewwise_exe

    if not _rewwise_exe or not _rewwise_exe.is_file():
        _rewwise_exe = filedialog.askopenfilename(
            defaultextension="exe", filetypes=[("bnk2json", "exe")]
        )

    return _rewwise_exe


def unpack_soundbank(bnk_path: Path) -> Path:
    rewwise_exe = get_rewwise_path()

    print(f"Unpacking soundbank {bnk_path.name}")
    subprocess.check_call([rewwise_exe, str(bnk_path)])

    return bnk_path.parent / bnk_path.stem / "soundbank.json"


def repack_soundbank(bnk_dir: Path) -> Path:
    rewwise_exe = get_rewwise_path()

    if bnk_dir.name == "sounbank.json":
        bnk_dir = bnk_dir.parent

    print(f"Repacking soundbank {bnk_dir.stem}")
    subprocess.check_call([rewwise_exe, str(bnk_dir)])

    # TODO rename the backup and new soundbank

    return bnk_dir.parent / bnk_dir.stem + ".bnk"


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


def get_lookup_table() -> dict[int, str]:
    import pybnk

    keys = resources.read_text(pybnk, "resources/wwise_ids.txt")
    return {calc_hash(k): k for k in keys if not k.startswith("#")}


lookup_table = get_lookup_table()
