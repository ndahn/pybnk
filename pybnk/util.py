from typing import Any, TYPE_CHECKING
from pathlib import Path
import logging
import subprocess
import shutil
import networkx as nx

from pybnk.external import get_rewwise

if TYPE_CHECKING:
    from pybnk import Soundbank


logger = logging.getLogger("pybnk")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def unpack_soundbank(bnk_path: Path) -> Path:
    rewwise_exe = get_rewwise()

    logger.info(f"Unpacking soundbank {bnk_path.name}")
    subprocess.check_call([rewwise_exe, str(bnk_path)])

    return bnk_path.parent / bnk_path.stem / "soundbank.json"


def repack_soundbank(bnk_dir: Path) -> Path:
    rewwise_exe = get_rewwise()

    if bnk_dir.name == "sounbank.json":
        bnk_dir = bnk_dir.parent

    logger.info(f"Repacking soundbank {bnk_dir.stem}")
    subprocess.check_call([rewwise_exe, str(bnk_dir)])

    # Rename the backup and new soundbank to make things a little easier for the user
    old_file = bnk_dir.parent / bnk_dir.stem + ".bnk"
    new_file = bnk_dir.parent / bnk_dir.stem + ".created.bnk"
    shutil.move(old_file, str(old_file) + ".bak")
    shutil.move(new_file, old_file)

    return bnk_dir.parent / bnk_dir.stem + ".bnk"


def format_hierarchy(bnk: "Soundbank", graph: nx.DiGraph) -> str:
    visited = set()
    ret = ""

    def delve(nid: Any, prefix: str):
        nonlocal ret

        if nid in visited:
            return

        visited.add(nid)
        children = list(graph.successors(nid))

        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            branch = "└──" if is_last else "├──"
            ret += (f"{prefix}{branch} {child}\n")

            new_prefix = prefix + ("    " if is_last else "│   ")
            delve(child, new_prefix)

    # Find root node
    roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
    if not roots:
        logger.warning("Could not determine root node")
        return

    root = roots[0]
    if len(roots) > 1:
        logger.warning(f"Multiple roots found, using {root}")

    delve(root, "")
    return ret.rstrip("\n")
