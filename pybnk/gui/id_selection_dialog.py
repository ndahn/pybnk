#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from pybnk import Soundbank
from pybnk.gui.localization import Localization


class IdSelectionDialog(tk.Toplevel):
    """Dialog for selecting IDs from soundbank and adding them to main window text boxes"""

    def __init__(self, parent, bnk: Soundbank, lang: Localization):
        super().__init__(parent)

        self.parent = parent
        self.soundbank = bnk
        self.lang = lang

        self.title(self.lang["select_ids_dialog_title"])
        self.geometry("400x500")
        self.transient(parent)  # Set to be on top of parent

        # Create UI
        self._create_widgets()

        # Load IDs
        self._populate_id_list()

    def _create_widgets(self) -> None:
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Help message
        help_left = ttk.Label(
            main_frame,
            text=self.lang["select_ids_tooltip"],
            foreground="blue",
            wraplength=360,
        )
        help_left.pack(anchor=tk.W, pady=(0, 5))

        # Label
        label = ttk.Label(main_frame, text=self.lang["available_ids_label"])
        label.pack(anchor=tk.W, pady=(0, 5))

        # Listbox with scrollbar
        list_container = tk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.id_listbox = tk.Listbox(
            list_container, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set
        )
        self.id_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.id_listbox.yview)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        add_button = ttk.Button(
            button_frame,
            text=self.lang["add_selected_button"],
            command=self._add_selected_ids,
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))

    def _populate_id_list(self) -> None:
        """Load soundbank and populate ID list"""
        self.id_listbox.delete(0, tk.END)
        self.id_listbox.insert(tk.END, self.lang["loading_ids"])

        def load_in_thread():
            try:
                play_events = self.soundbank.find_events("Play")

                play_event_names = []
                for evt in play_events:
                    name = evt.lookup_name()
                    if name:
                        if name.startswith("Play_"):
                            name = name[5:]
                            play_event_names.append(name)
                    # TODO should we include raw hashes? 
                    # If so, make sure they are handled properly
                    #else:
                    #    name = f"#{evt.id}"

                play_event_names.sort()

                # Update UI in main thread
                self.after(0, self._update_listbox, play_event_names)
            except Exception as e:
                self.after(
                    0,
                    lambda exc=e: messagebox.showerror(self.lang["error"], str(exc)),
                )
                self.after(0, self.id_listbox.delete, 0, tk.END)

        threading.Thread(target=load_in_thread, daemon=True).start()

    def _update_listbox(self, ids: list) -> None:
        """Helper function to update Listbox in main thread"""
        self.id_listbox.delete(0, tk.END)
        for sound_id in ids:
            self.id_listbox.insert(tk.END, sound_id)

    def _add_selected_ids(self) -> None:
        """Add selected IDs to main window text boxes"""
        selected_indices = self.id_listbox.curselection()

        for i in selected_indices:
            src_id = self.id_listbox.get(i)

            # Auto-generate destination ID (simple replacement of 'c' with 's')
            if src_id.startswith("c"):
                dst_id = "s" + src_id[1:]
            else:
                dst_id = src_id  # Keep original if doesn't start with 'c'

            self.parent.src_wwise_ids.insert(tk.END, f"{src_id}\n")
            self.parent.dst_wwise_ids.insert(tk.END, f"{dst_id}\n")

        self.destroy()
