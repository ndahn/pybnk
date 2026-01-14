from typing import Any, TYPE_CHECKING
from pathlib import Path
from importlib import resources
import subprocess
import shutil
import networkx as nx
from tkinter import filedialog

if TYPE_CHECKING:
    from pybnk import Soundbank


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


def print_hierarchy(bnk: "Soundbank", graph: nx.DiGraph):
    visited = set()

    def delve(nid: Any, prefix: str):
        if nid in visited:
            return

        visited.add(nid)
        children = list(graph.successors(nid))
        
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            branch = "└──" if is_last else "├──"
            print(f"{prefix}{branch} {child}")
            
            new_prefix = prefix + ("    " if is_last else "│   ")
            delve(graph, child, new_prefix, visited)

    # Find root node
    roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
    if not roots:
        print("Warning: Could not determine root node")
        return

    root = roots[0]
    if len(roots) > 1:
        print(f"Warning: Multiple roots found, using {root}")
    
    delve(root, "", None)


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
