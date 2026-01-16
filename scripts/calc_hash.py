#!/usr/bin/env python3
import sys

from pybnk.util import calc_hash


if __name__ == "__main__":
    
    for arg in sys.argv[1:]:
        h = calc_hash(arg)
        print(f"{arg}:\t{h}")
