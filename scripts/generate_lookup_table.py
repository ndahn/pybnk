from pathlib import Path

from pybnk.enums import SoundType
from pybnk.hash import calc_hash


def generate_lookup_table(input: Path, output: Path) -> None:
    with Path(output).open("w") as fout:
        with Path(input).open() as fin:
            while True:
                line = fin.readline()
                if not line:
                    break

                if line.startswith("#"):
                    continue

                h = calc_hash(line)
                fout.write(f"{h}:{line}")


def generate_names() -> list[str]:
    # Experimental function, trying to fill some of the remaining gaps
    names = []
    for action in ("Play_", "Stop_"):
        for sound_type in "s":
            for i in range(1000):
                for j in range(100000):
                    names.append(action + sound_type + str(i * 10) + "{:05d}".format(j))

    print(f"Generated {len(names)} unique names")
    return names


if __name__ == "__main__":
    res_dir = Path(__file__).parent.parent / "resources"
    input = res_dir / "wwise_ids.txt"
    output = res_dir / "lookup_dict.txt"

    import time
    now = time.time()
    generate_lookup_table(input, output)
    print(f"Generated new lookup table in {time.time() - now}s")

