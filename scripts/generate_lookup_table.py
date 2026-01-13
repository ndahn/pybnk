from pathlib import Path

from pybnk.common.util import calc_hash


def generate_lookup_table(input: Path, output: Path) -> None:
    with output.open("w") as fout:
        with input.open() as fin:
            while True:
                line = fin.readline()
                if not line:
                    break

                if line.startswith("#"):
                    continue

                h = calc_hash(line)
                fout.write(f"{line[:-1]}:{h}\n")


if __name__ == "__main__":
    res_dir = Path(__file__).parent.parent / "pybnk/resources"
    input = res_dir / "wwise_ids.txt"
    output = Path(__file__).parent / "lookup_dict.txt"

    import time
    now = time.time()
    generate_lookup_table(input, output)
    print(f"Generated new lookup table in {time.time() - now}s")

