from typing import Literal
import os
from pathlib import Path
import shutil
import subprocess

# NOTE need to manually install audioop-lts
from pydub import AudioSegment, silence

from pybnk import Soundbank
from pybnk.util import logger
from pybnk.external import get_wwise, get_vgmstream_cli


def import_wems(bnk: Soundbank, wems: list[Path]) -> None:
    for wem in wems:
        if not wem.endswith(".wem"):
            continue

        # We allow adding a prefix to the wem ID to make them easier to handle
        if "_" in wem.name:
            _, wem_id = wem.stem.rsplit("_", maxsplit=1)
            wem_id = int(wem_id)
        else:
            wem_id = int(wem.stem)

        target_path = bnk.bnk_dir / f"{wem_id}.wem"
        shutil.copy(wem, target_path)

        sound_nodes = list(
            bnk.query(
                {
                    "type": "Sound",
                    "bank_source_data/media_information/source_id": wem_id,
                }
            )
        )

        wem_size = os.path.getsize(str(target_path))
        for node in sound_nodes:
            node["bank_source_data/media_information/in_memory_media_size"] = wem_size


def set_volume(wav: Path, volume: float, *, out_file: Path = None) -> Path:
    audio: AudioSegment = AudioSegment.from_file(wav)
    audio = audio.apply_gain(volume)
    audio.export(str(out_file or wav), format="wav")
    return out_file


def create_prefetch_snippet(
    wav: Path, length: float = 1.0, *, out_file: Path = None
) -> Path:
    audio: AudioSegment = AudioSegment.from_file(str(wav))
    audio = audio[: length * 1000]
    audio.export(str(out_file or wav), format="wav")
    return Path(out_file or wav)


def trim_silence(
    wav: Path,
    threshold: float = None,
    *,
    min_silence_length: float = 0.5,
    start_end_tolerance: float = 0.5,
    out_file: Path = None,
) -> Path:
    audio: AudioSegment = AudioSegment.from_file(str(wav))

    if not threshold:
        threshold = audio.dBFS

    quiets = silence.detect_silence(
        audio,
        min_silence_len=min_silence_length,
        silence_thresh=threshold,
    )
    start = 0
    end = len(audio)

    # A quiet section close to the beginning
    if quiets and quiets[0][0] <= start_end_tolerance * 1000:
        start = quiets[0][1]

    # A quiet section close to the end
    if len(quiets) > 1 and quiets[-1][1] >= len(audio) - start_end_tolerance * 1000:
        end = quiets[-1][0]

    audio = audio[start:end]
    audio.export(str(out_file or wav), format="wav")
    return Path(out_file or wav)


def wav2wem(
    waves: list[Path] | Path,
    out_dir: Path = None,
    conversion: Literal["PCM", "Vorbis Quality High"] = "Vorbis Quality High",
) -> Path:
    wwise = get_wwise()

    if isinstance(waves, Path):
        waves = [waves]

    wav_dir = waves[0].parent
    if not out_dir:
        out_dir = wav_dir

    source_lines = []
    for wav in waves:
        if not wav.is_file():
            logger.error(f"FileNotFound: {wav}")
            continue

        # NOTE as long as all paths are absolute this should be fine
        source_lines.append(
            f'<Source Path="{wav.absolute()}" Conversion="{conversion}"/>'
        )

    # Create a list of files to convert
    # Thanks to https://github.com/EternalLeo/sound2wem for the template!
    wsources_path = wav_dir / "list.wsources"
    wsources_path.write_text(
        f"""\
<?xml version="1.0" encoding="UTF-8"?>
<ExternalSourcesList SchemaVersion="1" Root="{wav_dir}">
	{"\n".join(source_lines)}
</ExternalSourcesList>
"""
    )

    # Create a wwise project if it doesn't exist yet
    wproj_path = wav_dir / "pybnk/pybnk.wproj"
    if not wproj_path.is_file():
        subprocess.check_call([wwise, "create-new-project", str(wproj_path), "--quiet"])

    # Convert the wav files by passing the wsources list to wwise
    subprocess.check_call(
        [
            wwise,
            "convert-external-source",
            str(wproj_path),
            "--source-file",
            str(wsources_path),
            "--output",
            str(out_dir),
            "--quiet",
        ]
    )

    # Generated files will be stored in a Windows folder (on Windows)
    wwise_out_dir = out_dir / "Windows"
    for file in wwise_out_dir.glob("*"):
        shutil.move(file, out_dir)

    # Cleanup
    shutil.rmtree(wwise_out_dir)
    wsources_path.unlink()

    return Path(out_dir)


def wem2wav(wems: list[Path] | Path, out_dir: Path = None,) -> None:
    vgmstream = get_vgmstream_cli()

    if isinstance(wems, Path):
        wems = [wems]

    wav_dir = wems[0].parent
    if not out_dir:
        out_dir = wav_dir

    try:
        for wem in wems:
            if not wem.is_file():
                logger.error(f"FileNotFound: {wem}")
                continue

            subprocess.check_call(
                [
                    vgmstream,
                    "-o",
                    wem.parent / wem.stem + ".wav",
                    str(wem),
                ]
            )
    except subprocess.CalledProcessError as e:
        logger.error(
            "Conversion failed! Make sure you have the required libraries installed!\n"
            " -> https://github.com/vgmstream/vgmstream/blob/master/doc/USAGE.md"
        )
        raise e
