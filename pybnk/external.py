from functools import lru_cache
from tkinter import filedialog


@lru_cache
def get_file(name: str, extension: str) -> str:
    ret = filedialog.askopenfilename(
        defaultextension=extension, filetypes=[(name, extension)], title=f"Locate {name}"
    )

    if not ret:
        raise FileNotFoundError(f"{name} not found")

    return ret


def get_rewwise() -> str:
    return get_file("bnk2json", "exe")


def get_wwise() -> str:
    return get_file("WwiseConsole", "exe")


def get_vgmstream_cli() -> str:
    return get_file("vgmstream-cli", "exe")
