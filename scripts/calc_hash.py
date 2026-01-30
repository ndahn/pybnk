#!/usr/bin/env python3
import sys
import tkinter as tk

from pybnk.util import calc_hash
from pybnk.gui.calc_hash_dialog import CalcHashDialog
from pybnk.gui.localization import English


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            h = calc_hash(arg)
            print(f"{arg}:\t{h}")
    else:
        app = tk.Tk()
        app.withdraw()
        dlg = CalcHashDialog(None, English())
        app.mainloop()
