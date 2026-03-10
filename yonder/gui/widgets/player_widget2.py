from typing import Any, Callable
from pathlib import Path
import tempfile
import atexit
import wave
import numpy as np
from dearpygui import dearpygui as dpg

from yonder.util import logger
from yonder.gui.config import get_config
from yonder.wem import wem2wav
from yonder.player import WavPlayer
from yonder.gui import style


_wav_tmp_dir = tempfile.TemporaryDirectory("_player", "yonder_")
atexit.register(_wav_tmp_dir.cleanup)


def add_wav_player(
    get_audio_path: Callable[[], Path],
    markers: list[tuple[str, float, tuple[int, int, int]]] = None,
    on_marker_changed: Callable[[str, tuple[str, float], Any], None] = None,
    *,
    tag: str = 0,
    parent: str = 0,
    user_data: Any = None,
) -> str:
    if not tag:
        tag = dpg.generate_uuid()

    last_path: Path = None
    player: WavPlayer = None

    def get_wav_path(audio: Path) -> Path:
        if audio is None or not audio.is_file():
            logger.error(f"Audio {audio} does not exist")
            return None

        if audio.name.endswith(".wem"):
            wav = Path(_wav_tmp_dir.name) / (audio.stem + ".wav")
            if not wav.is_file():
                vgmstream = get_config().locate_vgmstream()
                logger.info(f"Converting {audio} to wav for playback")
                wav = wem2wav(Path(vgmstream), audio, Path(_wav_tmp_dir.name))[0]
            return wav

        elif audio.name.endswith(".wav"):
            return audio

        else:
            logger.error(f"Audio must be a wav or wem file ({audio})")
            return None

    def create_player(audio: Path) -> WavPlayer:
        wav = get_wav_path(audio)
        if wav:
            player = WavPlayer(str(wav))
            return player

    def on_play_pause() -> None:
        nonlocal player, last_path
        audio = get_audio_path()

        if player and last_path != audio:
            # Audio changed
            player.stop()
            player = None

        if not player:
            player = create_player(audio)
            if not player:
                return

            dpg.configure_item(f"{tag}_progress", default_value=0.0, label="0.000")
            last_path = audio
            regenerate(audio)

        if player.playing:
            player.pause()
        else:
            if player.position >= player.duration:
                player.seek(0.0)

            player.play()
            progress_update()

    def on_progress_changed(sender: str, pos: float, user_data: Any) -> None:
        if player:
            player.seek(pos)

    def progress_update() -> None:
        if not player or not player.playing:
            return

        # In case the player widget got destroyed
        if not dpg.does_item_exist(f"{tag}_progress"):
            player.stop()
            return

        dpg.configure_item(
            f"{tag}_progress",
            default_value=player.position,
            label=f"{player.position:.03f}",
        )
        dpg.set_frame_callback(dpg.get_frame_count() + 2, progress_update)

    def on_marker_update(sender: str, pos: float, cb_user_data: Any) -> None:
        marker = dpg.get_item_label(sender)
        on_marker_changed(tag, (marker, pos), user_data)

    def regenerate(audio: Path) -> None:
        dpg.delete_item(f"{tag}_axis_y", children_only=True)

        with wave.open(str(audio), "r") as f:
            frames = np.frombuffer(f.readframes(-1), np.int16)

            # Split into channels
            channels = [[]] * f.getnchannels()
            for index, datum in enumerate(frames):
                channels[index % len(channels)].append(datum)

            time = np.linspace(
                0,
                len(frames) / (len(channels) * f.getframerate()),
                num=len(frames) // len(channels),
            )

        # Plot waveforms
        for i, (signal, sign) in enumerate(zip(channels, [1, -1])):
            # TODO colors
            if i != 0:
                break
            dpg.add_line_series(
                time,
                sign * signal,
                shaded=True,
                tag=f"{tag}_channel_{i}",
                label=f"Ch{i}",
                parent=f"{tag}_axis_y",
            )

        dpg.fit_axis_data(f"{tag}_axis_x")
        dpg.fit_axis_data(f"{tag}_axis_y")

    with dpg.group():
        with dpg.plot(
            height=120,
            width=-1,
            no_box_select=True,
            no_title=True,
            tag=tag,
            parent=parent,
        ):
            dpg.add_plot_axis(
                dpg.mvXAxis,
                label="x",
                no_label=True,
                no_highlight=True,
                lock_min=True,
                pan_stretch=True,
                tag=f"{tag}_axis_x",
                no_tick_labels=True,
            )
            dpg.add_plot_axis(
                dpg.mvYAxis,
                label="y",
                no_label=True,
                no_highlight=True,
                lock_min=True,
                pan_stretch=True,
                tag=f"{tag}_axis_y",
            )

            # Playback marker
            dpg.add_drag_line(
                show_label=False,
                thickness=2,
                color=style.red,
                callback=on_progress_changed,
                tag=f"{tag}_progress",
            )

            # User markers
            if markers:
                for label, pos, color in markers:
                    dpg.add_drag_line(
                        label=label,
                        color=color,
                        default_value=pos,
                        callback=on_marker_update,
                    )

        # TODO theme
        dpg.add_button(
            pos=(10, 10),
            arrow=True,
            direction=dpg.mvDir_Right,
            callback=on_play_pause,
        )

    regenerate(get_wav_path(get_audio_path()))
    return tag
