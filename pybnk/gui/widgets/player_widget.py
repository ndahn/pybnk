from typing import Any, Callable
from pathlib import Path
import tempfile
import atexit
from dearpygui import dearpygui as dpg

from pybnk.util import logger
from pybnk.gui.config import Config
from pybnk.wem import wem2wav
from pybnk.player import WavPlayer


_wav_tmp_dir = tempfile.TemporaryDirectory("_player", "pybnk_")
atexit.register(_wav_tmp_dir.cleanup)


def add_wav_player(
    config: Config,
    get_sound: Callable[[], Path],
    *,
    tag: str = 0,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    player: WavPlayer = None

    def create_player(audio: Path) -> WavPlayer:
        if audio.name.endswith(".wem"):
            wav = Path(_wav_tmp_dir.name) / (audio.stem + ".wav")
            if not wav.is_file():
                vgmstream = config.locate_vgmstream()
                logger.info(f"Converting {audio} to wav for playback")
                wav = wem2wav(Path(vgmstream), [audio], Path(_wav_tmp_dir.name))[0]
        elif audio.name.endswith(".wav"):
            wav = audio
        else:
            raise ValueError(f"Audio must be a wav or wem file ({audio})")

        player = WavPlayer(str(wav))
        return player

    def on_play_pause() -> None:
        nonlocal player
        audio = get_sound()

        if player and player._path != str(audio):
            # Audio changed
            player.stop()
            player = None

        if not player:
            player = create_player(audio)

        if player.playing:
            player.pause()
        else:
            player.play()
            progress_update()

    def on_stop() -> None:
        if player:
            player.stop()

    def on_progress_changed(sender: str, progress: float, user_data: Any) -> None:
        if player:
            player.seek(progress)

    def progress_update() -> None:
        if not player or not player.playing:
            return

        dpg.configure_item(
            f"{tag}_progress", default_value=player.position, max_value=player.duration
        )
        dpg.set_value(
            f"{tag}_progress_text", f"{player.position:.2f} / {player.duration:.2f}"
        )

        dpg.set_frame_callback(dpg.get_frame_count() + 2, progress_update)

    with dpg.group(horizontal=True, tag=tag):
        dpg.add_button(
            arrow=True,
            direction=dpg.mvDir_Right,
            callback=on_play_pause,
            tag=f"{tag}_play_pause",
        )
        dpg.add_button(
            label="x",
            callback=on_stop,
            tag=f"{tag}_stop",
        )

        with dpg.group():
            dpg.add_slider_float(
                min_value=0.0,
                max_value=1.0,
                clamped=True,
                no_input=True,
                callback=on_progress_changed,
                tag=f"{tag}_progress",
            )
            dpg.add_text(
                "0.00 / 0.00",
                tag=f"{tag}_progress_text",
            )
