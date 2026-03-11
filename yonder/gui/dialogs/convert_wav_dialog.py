from typing import Any, Callable
from pathlib import Path
from dearpygui import dearpygui as dpg

from yonder.gui import style
from yonder.gui.config import Config
from yonder.gui.widgets import (
    add_generic_widget,
    add_filepaths_table,
    loading_indicator,
)
from yonder.util import logger
from yonder.wem import wav2wem, trim_silence, set_volume, create_prefetch_snippet


def convert_wavs_dialog(
    config: Config,
    callback: Callable[[list[Path]], None] = None,
    *,
    title: str = "Convert Wave Files",
    tag: str = None,
) -> str:
    if not tag:
        tag = dpg.generate_uuid()
    elif dpg.does_item_exist(tag):
        dpg.delete_item(tag)

    output_dir: Path = None
    wav_paths: list[Path] = []

    def on_wavs_changed(sender: str, paths: list[Path], user_data: Any) -> None:
        nonlocal output_dir

        wav_paths.clear()
        wav_paths.extend(paths)

        if paths and output_dir is None:
            output_dir = paths[0].parent
            dpg.set_value(f"{tag}_output_dir", str(output_dir))

    def on_outputdir_selected(sender: str, path: Path, user_data: Any) -> None:
        nonlocal output_dir
        output_dir = path

    def show_message(
        msg: str = None, color: tuple[int, int, int, int] = style.red
    ) -> None:
        if not msg:
            dpg.hide_item(f"{tag}_notification")
            return

        dpg.configure_item(
            f"{tag}_notification",
            default_value=msg,
            color=color,
            show=True,
        )

    def on_okay() -> None:
        if not wav_paths:
            show_message("No wave files selected")
            return

        if not output_dir or not output_dir.is_dir():
            show_message("Invalid output directory")
            return

        if dpg.get_value(f"{tag}_convert_to_wem"):
            try:
                wwise_exe = config.locate_wwise()
            except Exception:
                show_message("Wwise exe not found")
                return

        show_message()

        loading = loading_indicator("Converting...")
        try:
            out_files = list(wav_paths)

            if dpg.get_value(f"{tag}_trim_silence"):
                logger.info("Trimming silence...")
                dpg.set_value(f"{loading}_label", "Trimming silence...")
                silence_threshold = dpg.get_value(f"{tag}_silence_threshold")

                for i, wav in enumerate(out_files):
                    trim_silence(wav, silence_threshold, out_file=output_dir / wav.name)
                    out_files[i] = output_dir / wav.name

            if dpg.get_value(f"{tag}_create_prefetch_snippet"):
                logger.info("Creating prefetch snippets...")
                dpg.set_value(f"{loading}_label", "Creating prefetch snippets...")
                snippet_length = dpg.get_value(f"{tag}_snippet_legnth")

                for i, wav in enumerate(out_files):
                    create_prefetch_snippet(
                        wav, snippet_length, out_file=output_dir / wav.name
                    )
                    out_files[i] = output_dir / wav.name

            if dpg.get_value(f"{tag}_adjust_volume"):
                logger.info("Adjusting volume...")
                dpg.set_value(f"{loading}_label", "Adjusting volume...")
                target_volume = dpg.get_value(f"{tag}_target_volume")

                for i, wav in enumerate(out_files):
                    set_volume(wav, target_volume, out_file=output_dir / wav.name)
                    out_files[i] = output_dir / wav.name

            if dpg.get_value(f"{tag}_convert_to_wem"):
                logger.info("Converting wave files...")
                dpg.set_value(f"{loading}_label", "Converting waves...")
                out_files = wav2wem(wwise_exe, out_files, out_dir=output_dir)
        finally:
            dpg.delete_item(loading)

        if callback:
            callback(out_files)

        show_message("Yay!", color=style.blue)
        dpg.set_item_label(f"{tag}_button_okay", "Again?")

    with dpg.window(
        label=title,
        width=400,
        height=400,
        autosize=True,
        no_saved_settings=True,
        tag=tag,
        on_close=lambda: dpg.delete_item(window),
    ) as window:
        add_filepaths_table(
            [],
            on_wavs_changed,
            title="Wave files",
            filetypes={"Wave (.wav)": "*.wav"},
            tag=f"{tag}_wavs_table",
        )

        dpg.add_spacer(height=5)

        add_generic_widget(
            Path,
            "Output dir",
            on_outputdir_selected,
            file_mode="folder",
            tag=f"{tag}_output_dir",
        )

        dpg.add_spacer(height=5)

        with dpg.group(horizontal=True):
            dpg.add_checkbox(
                label="",
                default_value=False,
                tag=f"{tag}_adjust_volume",
            )
            dpg.add_slider_float(
                label="Target volume",
                default_value=-3.0,
                min_value=-96.0,
                max_value=96.0,
                tag=f"{tag}_target_volume",
            )

        with dpg.group(horizontal=True):
            dpg.add_checkbox(
                label="",
                default_value=False,
                tag=f"{tag}_trim_silence",
            )
            dpg.add_slider_float(
                label="Silence threshold",
                default_value=0.0,
                min_value=-10.0,
                max_value=10.0,
                tag=f"{tag}_silence_threshold",
            )

        with dpg.group(horizontal=True):
            dpg.add_checkbox(
                label="",
                default_value=False,
                tag=f"{tag}_create_prefetch_snippet",
            )
            dpg.add_slider_float(
                label="Snippet length",
                default_value=1.0,
                min_value=-0.5,
                max_value=10.0,
                tag=f"{tag}_snippet_length",
            )

        dpg.add_spacer(height=5)

        dpg.add_checkbox(
            label="Convert to .wem",
            default_value=True,
            tag=f"{tag}_convert_to_wem",
        )

        dpg.add_separator()
        dpg.add_text(show=False, tag=f"{tag}_notification", color=style.red)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Beat it!", callback=on_okay, tag=f"{tag}_button_okay")
