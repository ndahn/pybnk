import sys
from os import path
import yaml
import inspect
from pathlib import Path
from dataclasses import dataclass, field, asdict

from pybnk.gui.dialogs.file_dialog import open_file_dialog


@dataclass
class Config:
    recent_files: list[str] = field(default_factory=list)

    bnk2json_exe: str = None
    wwise_exe: str = None
    vgmstream_exe: str = None

    # Your advertisement could be here

    def add_recent_file(self, file_path: str) -> None:
        file_path = path.normpath(path.abspath(file_path))
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]

    def remove_recent_file(self, file_path: str) -> None:
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

    def save(self, config_path: str = None) -> None:
        if not config_path:
            config_path = get_default_config_path()

        with open(config_path, "w") as f:
            yaml.safe_dump(asdict(self), f)

    def locate_bnk2json(self) -> str:
        if not self.bnk2json_exe or not Path(self.bnk2json_exe).is_file():
            bnk2json_exe = open_file_dialog(
                title="Locate bnk2json.exe", filetypes={"bnk2json.exe": "bnk2json.exe"}
            )
            if not bnk2json_exe:
                raise ValueError("bnk2json not found")

            self.bnk2json_exe = bnk2json_exe
            self.save()

        return self.bnk2json_exe

    def locate_wwise(self) -> str:
        if not self.wwise_exe or not Path(self.wwise_exe).is_file():
            wwise_exe = open_file_dialog(
                title="Locate WwiseConsole.exe",
                filetypes={"WwiseConsole.exe": "WwiseConsole.exe"},
            )
            if not wwise_exe:
                raise ValueError("WwiseConsole not found")

            self.wwise_exe = wwise_exe
            self.save()

        return self.wwise_exe

    def locate_vgmstream(self) -> str:
        if (
            not self.vgmstream_exe
            or not Path(self.vgmstream_exe).is_file()
        ):
            vgmstream_exe = open_file_dialog(
                title="Locate vgmstream-cli.exe",
                filetypes={"vgmstream-cli.exe": "vgmstream-cli.exe"},
            )
            if not vgmstream_exe:
                raise ValueError("vgmstream-cli not found")

            self.vgmstream_exe = vgmstream_exe
            self.save()

        return self.vgmstream_exe


_config: Config = None


def get_default_config_path() -> str:
    return path.join(path.dirname(sys.argv[0]), "config.yaml")


def get_config() -> Config:
    return _config


def load_config(config_path: str = None) -> Config:
    global _config
    
    if not config_path:
        config_path = get_default_config_path()

    if path.isfile(config_path):
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        
        sig = inspect.signature(Config.__init__)
        kw = {}
        
        # Match the args from the config to the current implementation in case it changed
        for key, val in cfg.items():
            if key in sig.parameters:
                kw[key] = val

        _config = Config(**kw)
    else:
        print(f"Creating new config in {config_path}")
        _config = Config()
        _config.save(config_path)

    return _config
