#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import traceback
import threading

from pybnk import Soundbank
from pybnk.transfer import copy_structure
from pybnk.gui.localization import Localization, English, Chinese
from pybnk.gui.calc_hash_dialog import CalcHashDialog
from pybnk.gui.id_selection_dialog import IdSelectionDialog
from pybnk.gui.loading_dialog import LoadingDialog
from pybnk.gui.tooltip import ToolTip


class TransferSoundsDialog(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- I18N and Widget Storage ---
        self.lang: Localization = English()  # Default language
        self.widgets = {}  # Store components that need text updates
        self.tooltips = []  # Store all ToolTip instances

        self.title(self.lang["title"])
        self.geometry("550x600")

        self.src_bank_path: str = ""
        self.dst_bank_path: str = ""

        # Create UI
        self._create_widgets()
        self._update_ui_text()  # Initialize UI text with default language

    def _create_widgets(self) -> None:
        # --- Language selection ---
        lang_frame = ttk.Frame(self, padding="10")
        lang_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=(0, 5))
        self.lang_combo = ttk.Combobox(
            lang_frame, values=["English", "中文"], state="readonly"
        )
        self.lang_combo.set("English")
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._change_language)

        # File selection frame
        file_frame = ttk.Frame(self, padding="10")
        file_frame.pack(fill=tk.X)

        # File 1 with help icon in front
        help1 = ttk.Label(file_frame, text="ℹ", foreground="blue", cursor="hand2")
        help1.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tooltips.append(ToolTip(help1, "select_source_tooltip", self.lang))

        self.widgets["source_soundbank_label"] = ttk.Label(file_frame)
        self.widgets["source_soundbank_label"].grid(
            row=0, column=1, sticky=tk.W, padx=(5, 10), pady=5
        )

        self.src_bank_label = ttk.Label(
            file_frame,
            text=self.lang["no_file_selected"],
            foreground="gray",
        )
        self.src_bank_label.grid(row=0, column=2, sticky=tk.W, padx=10)

        self.widgets["browse_src_button"] = ttk.Button(
            file_frame, command=self._browse_src_bank
        )
        self.widgets["browse_src_button"].grid(row=0, column=3)

        help2 = ttk.Label(file_frame, text="ℹ", foreground="blue", cursor="hand2")
        help2.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tooltips.append(ToolTip(help2, "select_dest_tooltip", self.lang))

        self.widgets["dest_soundbank_label"] = ttk.Label(file_frame)
        self.widgets["dest_soundbank_label"].grid(
            row=1, column=1, sticky=tk.W, padx=(5, 10), pady=5
        )

        self.dst_bank_label = ttk.Label(
            file_frame,
            text=self.lang["no_file_selected"],
            foreground="gray",
        )
        self.dst_bank_label.grid(row=1, column=2, sticky=tk.W, padx=10)

        self.widgets["browse_dst_button"] = ttk.Button(
            file_frame, command=self._browse_dst_bank
        )
        self.widgets["browse_dst_button"].grid(row=1, column=3)

        # Text boxes frame
        text_frame = ttk.Frame(self, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Left text box
        left_frame = tk.Frame(text_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Label with tooltip for left box
        left_label_row = tk.Frame(left_frame)
        left_label_row.pack(anchor=tk.W)

        help_left = ttk.Label(
            left_label_row, text="ℹ", foreground="blue", cursor="hand2"
        )
        help_left.pack(side=tk.LEFT)
        self.tooltips.append(ToolTip(help_left, "source_ids_tooltip", self.lang))
        self.widgets["source_ids_label"] = ttk.Label(left_label_row)
        self.widgets["source_ids_label"].pack(side=tk.LEFT, padx=(5, 0))

        # Left text box with scrollbar
        left_scroll = ttk.Scrollbar(left_frame)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.src_wwise_ids = tk.Text(
            left_frame, width=20, height=10, yscrollcommand=left_scroll.set
        )
        self.src_wwise_ids.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scroll.config(command=self.src_wwise_ids.yview)

        # Right text box
        right_frame = tk.Frame(text_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Label with tooltip for right box
        right_label_row = tk.Frame(right_frame)
        right_label_row.pack(anchor=tk.W)

        help_right = ttk.Label(
            right_label_row, text="ℹ", foreground="blue", cursor="hand2"
        )
        help_right.pack(side=tk.LEFT)
        self.tooltips.append(ToolTip(help_right, "dest_ids_tooltip", self.lang))
        self.widgets["dest_ids_label"] = ttk.Label(right_label_row)
        self.widgets["dest_ids_label"].pack(side=tk.LEFT, padx=(5, 0))

        # Right text box with scrollbar
        right_scroll = ttk.Scrollbar(right_frame)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.dst_wwise_ids = tk.Text(
            right_frame, width=20, height=10, yscrollcommand=right_scroll.set
        )
        self.dst_wwise_ids.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scroll.config(command=self.dst_wwise_ids.yview)

        # --- Buttons to open ID selection and hash calculator dialogs ---
        select_ids_frame = ttk.Frame(self, padding="10 0 10 0")
        select_ids_frame.pack(fill=tk.X)

        self.widgets["open_id_dialog_button"] = ttk.Button(
            select_ids_frame, command=self._open_id_selection_dialog
        )
        self.widgets["open_id_dialog_button"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["open_hash_calculator_button"] = ttk.Button(
            select_ids_frame,
            text="Hash Calculator",
            command=self._open_hash_calculator_dialog,
        )
        self.widgets["open_hash_calculator_button"].pack(side=tk.LEFT)

        # Checkboxes
        check_frame = ttk.Frame(self, padding="10")
        check_frame.pack(fill=tk.X)

        self.enable_write_var = tk.BooleanVar(value=True)
        self.widgets["write_to_dest_check"] = ttk.Checkbutton(
            check_frame, variable=self.enable_write_var
        )
        self.widgets["write_to_dest_check"].pack(anchor=tk.W)

        # Separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        # Explanation text
        info_frame = ttk.Frame(self, padding="10")
        info_frame.pack(fill=tk.X)
        self.info_text = tk.Text(info_frame, height=4, wrap=tk.WORD)
        self.info_text.config(state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)

        # Start button
        self.widgets["transfer_button"] = ttk.Button(self, command=self._exec_transfer)
        self.widgets["transfer_button"].pack(pady=10)

    # --- Language change callback ---
    def _change_language(self, event=None):
        selected_language = self.lang_combo.get()
        if selected_language == "English":
            self.lang = English()
        elif selected_language == "中文":
            self.lang = Chinese()
        else:
            raise ValueError(f"Unknown translation {selected_language}")

        self._update_ui_text()

    # --- Function to update all UI text ---
    def _update_ui_text(self):
        self.title(self.lang["title"])
        # Update all components stored in self.widgets dictionary
        self.widgets["source_soundbank_label"].config(
            text=self.lang["source_soundbank_label"]
        )
        self.widgets["browse_src_button"].config(text=self.lang["browse"])
        self.widgets["dest_soundbank_label"].config(
            text=self.lang["dest_soundbank_label"]
        )
        self.widgets["browse_dst_button"].config(text=self.lang["browse"])
        self.widgets["source_ids_label"].config(text=self.lang["source_ids_label"])
        self.widgets["dest_ids_label"].config(text=self.lang["dest_ids_label"])
        self.widgets["write_to_dest_check"].config(
            text=self.lang["write_to_dest"]
        )
        self.widgets["transfer_button"].config(text=self.lang["transfer_button"])
        self.widgets["open_id_dialog_button"].config(
            text=self.lang["open_id_dialog_button"]
        )

        # Update explanation text
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", self.lang["info_text"])
        self.info_text.config(state=tk.DISABLED)

        # Update Tooltips (although ToolTip is generated dynamically, it's best to have a refresh mechanism)
        for tooltip in self.tooltips:
            tooltip.update_text()

    def _browse_src_bank(self) -> None:
        path = filedialog.askopenfilename(
            title=self.lang["select_source_json"],
            filetypes=[
                (self.lang["json_files"], "soundbank.json"),
                (self.lang["all_files"], "*.*"),
            ],
        )
        if path:
            print(f"Selected source soundbank: {path}")
            self.src_bank_path = path
            self.src_bank_label.config(text=Path(path).parent.name, foreground="black")

    def _browse_dst_bank(self) -> None:
        path = filedialog.askopenfilename(
            title=self.lang["select_dest_json"],
            filetypes=[
                (self.lang["json_files"], "soundbank.json"),
                (self.lang["all_files"], "*.*"),
            ],
        )
        if path:
            print(f"Selected destination soundbank: {path}")
            self.dst_bank_path = path
            self.dst_bank_label.config(text=Path(path).parent.name, foreground="black")

    def _open_id_selection_dialog(self) -> None:
        """Open ID selection dialog"""
        if not self.src_bank_path:
            messagebox.showwarning(
                self.lang["warning"], self.lang["select_source_first"]
            )
            return

        bnk = Soundbank.load(self.src_bank_path)
        IdSelectionDialog(self, bnk, self.lang)

    def _open_hash_calculator_dialog(self) -> None:
        """Open hash calculator dialog"""
        CalcHashDialog(self, self.lang)

    def _exec_transfer(self) -> None:
        try:
            # Source soundbank path
            if not self.src_bank_path:
                raise ValueError(self.lang["value_error_source_not_set"])
            src_bank_dir = Path(self.src_bank_path).parent
            if not src_bank_dir.is_dir():
                raise ValueError(self.lang["value_error_source_folder_not_exist"])

            # Destination soundbank path
            if not self.dst_bank_path:
                raise ValueError(self.lang["value_error_dest_not_set"])
            dst_bank_dir = Path(self.dst_bank_path).parent
            if not dst_bank_dir.is_dir():
                raise ValueError(self.lang["value_error_dest_folder_not_exist"])

            # Get text from both boxes and split by lines
            src_wwise_lines = self.src_wwise_ids.get("1.0", tk.END).strip().split("\n")
            dst_wwise_lines = self.dst_wwise_ids.get("1.0", tk.END).strip().split("\n")

            # Filter out possible empty lines
            src_wwise_lines = [line for line in src_wwise_lines if line.strip()]
            dst_wwise_lines = [line for line in dst_wwise_lines if line.strip()]

            if not src_wwise_lines:
                raise ValueError(self.lang["value_error_no_lines"])
            if len(src_wwise_lines) != len(dst_wwise_lines):
                raise ValueError(self.lang["value_error_line_mismatch"])

            wwise_map = {
                src.strip(): dst.strip()
                for src, dst in zip(src_wwise_lines, dst_wwise_lines)
            }

            enable_write = self.enable_write_var.get()
            loading = LoadingDialog(self, self.lang["transferring_sounds"])

            # Execute core logic in background thread
            def do_the_work():
                try:
                    src_bnk = Soundbank.load(src_bank_dir)
                    dst_bnk = Soundbank.load(dst_bank_dir)
                    copy_structure(src_bnk, dst_bnk, wwise_map)

                    if enable_write:
                        dst_bnk.save()

                except Exception as inner_exc:
                    traceback.print_exception(inner_exc)
                    loading.close()
                    self.after(
                        0,
                        lambda e=inner_exc: messagebox.showerror(
                            self.lang["error"], str(e)
                        ),
                    )
                else:
                    loading.close()
                    messagebox.showinfo(
                        self.lang["transfer_successful"],
                        self.lang["yay"],
                    )

            thread = threading.Thread(target=do_the_work, daemon=True)
            thread.start()
        except Exception as e:
            traceback.print_exception(e)
            messagebox.showerror(self.lang["transfer_failed"], str(e))


if __name__ == "__main__":
    app = TransferSoundsDialog()
    app.mainloop()
