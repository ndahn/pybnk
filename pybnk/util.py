from typing import Any, Callable, TYPE_CHECKING
import sys
from pathlib import Path
from dataclasses import dataclass
from docstring_parser import parse as doc_parse
import inspect
import builtins
import logging
import subprocess
import shutil
import networkx as nx

if TYPE_CHECKING:
    from pybnk import Soundbank


logger = logging.getLogger("pybnk")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def resource_dir() -> Path:
    return Path(sys.argv[0]).parent / "resources"


def resource_data(res_path: str, binary: bool = False) -> str | bytes:
    res = resource_dir() / res_path
    if binary:
        return res.read_bytes()
    return res.read_text()


def unpack_soundbank(bnk2json_exe: Path, bnk_path: Path) -> Path:
    subprocess.check_output([str(bnk2json_exe), str(bnk_path)])

    return bnk_path.parent / bnk_path.stem / "soundbank.json"


def repack_soundbank(bnk2json_exe: Path, bnk_dir: Path) -> Path:
    if bnk_dir.name == "sounbank.json":
        bnk_dir = bnk_dir.parent

    subprocess.check_output([str(bnk2json_exe), str(bnk_dir)])

    # Rename the backup and new soundbank to make things a little easier for the user
    old_file = bnk_dir.parent / (bnk_dir.stem + ".bnk")
    new_file = bnk_dir.parent / (bnk_dir.stem + ".created.bnk")
    shutil.move(old_file, str(old_file) + ".bak")
    shutil.move(new_file, old_file)

    return bnk_dir.parent / (bnk_dir.stem + ".bnk")


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


@dataclass
class FuncArg:
    undefined = object()

    name: str
    type: type
    default: Any = None
    doc: str = None


def get_function_spec(
    func: Callable, undefined: Any = FuncArg.undefined
) -> dict[str, FuncArg]:
    func_args = {}
    sig = inspect.signature(func)

    param_doc = {}
    if func.__doc__:
        parsed_doc = doc_parse(func.__doc__)
        param_doc = {p.arg_name: p.description for p in parsed_doc.params}

    # Create CLI options for click
    for param in sig.parameters.values():
        ptype = None
        default = undefined

        if param.annotation is not param.empty:
            ptype = param.annotation
            if ptype and isinstance(ptype, str):
                # If it's a primitive type we can parse it, otherwise ignore it
                # NOTE use the proper builtins module here, __builtins__ is unreliable
                ptype = getattr(builtins, ptype, None)

        if param.default is not inspect.Parameter.empty:
            default = param.default

            if ptype is None and default is not None:
                ptype = type(default)

        func_args[param.name] = FuncArg(
            param.name, ptype, default, param_doc.get(param.name)
        )

    return func_args


class PathDict(dict):
    @classmethod
    def convert(cls, d: dict) -> "PathDict":
        """Recursively converts a nested dict into a nested PathDict."""
        pd = PathDict()
        for key, value in d.items():
            pd[key] = cls.convert(value) if isinstance(value, dict) else value
        return pd

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str) and "/" in key:
            d = self
            for k in key.split("/"):
                d = d[k]
            return d

        return super().__getitem__(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        if isinstance(key, str) and "/" in key:
            d = self
            for k in key.split("/")[:-1]:
                d = d[k]
            d[key.rsplit("/", maxsplit=1)[-1]] = value
        else:
            super().__setitem__(key, value)
