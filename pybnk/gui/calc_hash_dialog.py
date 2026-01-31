#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk

from pybnk import calc_hash
from pybnk.gui.localization import Localization


class CalcHashDialog(tk.Toplevel):
    """Dialog for calculating hash of input string"""

    def __init__(self, parent, lang: Localization):
        super().__init__(parent)

        self.parent = parent
        self.lang = lang

        self.title(lang["calc_hash_window"])
        self.geometry("400x150")
        self.transient(parent)  # Set to be on top of parent

        # Create UI
        self._create_widgets()

    def _create_widgets(self) -> None:
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input label and entry
        input_label = ttk.Label(main_frame, text=self.lang["calc_hash_input"])
        input_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.input_entry = ttk.Entry(main_frame, width=50)
        self.input_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Bind to calculate hash on every change
        self.input_entry.bind("<KeyRelease>", self._calculate_hash)

        # Output label and entry
        output_label = ttk.Label(main_frame, text=self.lang["calc_hash_output"])
        output_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        self.output_entry = ttk.Entry(main_frame, width=50, state="readonly")
        self.output_entry.grid(row=3, column=0, sticky=(tk.W, tk.E))

        # Configure column weight for resizing
        main_frame.columnconfigure(0, weight=1)

    def _calculate_hash(self, event=None) -> None:
        """Calculate FNV-1 hash of input string and display in output field"""
        input_text = self.input_entry.get()

        if not input_text:
            # Clear output if input is empty
            self.output_entry.config(state="normal")
            self.output_entry.delete(0, tk.END)
            self.output_entry.config(state="readonly")
            return

        # Calculate FNV-1 32-bit hash
        hash_value = calc_hash(input_text)

        # Display hash in output field
        self.output_entry.config(state="normal")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, str(hash_value))
        self.output_entry.config(state="readonly")
