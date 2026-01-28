#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import traceback
import threading

from pybnk import Soundbank, calc_hash
from pybnk.transfer import copy_structure
from scripts.localization import Localization, English, Chinese


class ToolTip:
    def __init__(self, widget, text_key: str, lang):
        self.widget = widget
        self.text_key = text_key
        self.lang = lang
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None) -> None:
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        # Get text using translation function
        text = self.lang[self.text_key]
        label = tk.Label(
            self.tooltip,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=5,
            pady=3,
            wraplength=300,
            justify="left",
        )
        label.pack()

    def hide(self, event=None) -> None:
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    # Method for updating tooltip text when language changes
    def update_text(self):
        # The text is fetched dynamically in show(), so no action is needed here
        # unless we want to pre-fetch it. For simplicity, we'll let it be.
        pass


class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message: str = "Processing..."):
        super().__init__(parent)

        self.title("Please Wait")
        self.transient(parent)  # Set to be on top of parent
        self.grab_set()  # Block interaction with parent

        # Remove window decorations for a cleaner look
        self.overrideredirect(True)
        self.geometry("300x100")

        frame = tk.Frame(self, relief="solid", borderwidth=2, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Message
        tk.Label(frame, text=message, bg="white", font=("TkDefaultFont", 10)).pack(
            pady=20
        )

        # Progress bar
        self.progress = ttk.Progressbar(frame, mode="indeterminate", length=250)
        self.progress.pack(pady=10)
        self.progress.start(10)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def close(self):
        self.progress.stop()
        self.destroy()


class HashCalculatorDialog(tk.Toplevel):
    """Dialog for calculating hash of input string"""
    
    def __init__(self, parent, lang):
        super().__init__(parent)
        
        self.parent = parent
        self.lang = lang
        
        self.title("Hash Calculator")
        self.geometry("400x150")
        self.transient(parent)  # Set to be on top of parent
        
        # Create UI
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input label and entry
        input_label = ttk.Label(main_frame, text="Input String:")
        input_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.input_entry = ttk.Entry(main_frame, width=50)
        self.input_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Bind to calculate hash on every change
        self.input_entry.bind("<KeyRelease>", self._calculate_hash)
        
        # Output label and entry
        output_label = ttk.Label(main_frame, text="Hash (FNV-1 32-bit):")
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


class IdSelectionDialog(tk.Toplevel):
    """Dialog for selecting IDs from soundbank and adding them to main window text boxes"""
    
    def __init__(self, parent, src_bank_path: str, lang):
        super().__init__(parent)
        
        self.parent = parent
        self.src_bank_path = src_bank_path
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
        
        # Label
        label_row = tk.Frame(main_frame)
        label_row.pack(anchor=tk.W)

        help_left = ttk.Label(
            label_row, text="ℹ", foreground="blue", cursor="hand2"
        )
        help_left.pack(side=tk.LEFT)
        ToolTip(help_left, "select_ids_tooltip", self)

        label = ttk.Label(label_row, text=self.lang["available_ids_label"])
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # Listbox with scrollbar
        list_container = tk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.id_listbox = tk.Listbox(
            list_container, 
            selectmode=tk.EXTENDED, 
            yscrollcommand=scrollbar.set
        )
        self.id_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.id_listbox.yview)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        add_button = ttk.Button(
            button_frame, 
            text=self.lang["add_selected_button"],
            command=self._add_selected_ids
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        
    def _populate_id_list(self) -> None:
        """Load soundbank and populate ID list"""
        self.id_listbox.delete(0, tk.END)
        self.id_listbox.insert(tk.END, self.lang["loading_ids"])
        
        def load_in_thread():
            try:
                soundbank: Soundbank = Soundbank.load(self.src_bank_path)
                play_events = soundbank.find_events("Play")
                play_event_names = [evt.lookup_name(evt.id) for evt in play_events]
                play_event_names.sort()

                # Update UI in main thread
                self.after(0, self._update_listbox, play_event_names)
            except Exception as e:
                self.after(
                    0,
                    lambda exc=e: messagebox.showerror(
                        self.lang["error"], str(exc)
                    ),
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


class SoundbankHelperGui(tk.Tk):
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
        self.tooltips.append(ToolTip(help1, "select_source_tooltip", self))

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
        self.tooltips.append(ToolTip(help2, "select_dest_tooltip", self))

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
        self.tooltips.append(ToolTip(help_left, "source_ids_tooltip", self))
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
        self.tooltips.append(ToolTip(help_right, "dest_ids_tooltip", self))
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
            select_ids_frame, 
            command=self._open_id_selection_dialog
        )
        self.widgets["open_id_dialog_button"].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets["open_hash_calculator_button"] = ttk.Button(
            select_ids_frame,
            text="Hash Calculator",
            command=self._open_hash_calculator_dialog
        )
        self.widgets["open_hash_calculator_button"].pack(side=tk.LEFT)

        # Checkboxes
        check_frame = ttk.Frame(self, padding="10")
        check_frame.pack(fill=tk.X)

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
        self.widgets["browse_src_button"].config(
            text=self.lang["browse"]
        )
        self.widgets["dest_soundbank_label"].config(
            text=self.lang["dest_soundbank_label"]
        )
        self.widgets["browse_dst_button"].config(
            text=self.lang["browse"]
        )
        self.widgets["source_ids_label"].config(
            text=self.lang["source_ids_label"]
        )
        self.widgets["dest_ids_label"].config(
            text=self.lang["dest_ids_label"]
        )
        self.widgets["transfer_button"].config(
            text=self.lang["transfer_button"]
        )
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
                self.lang["warning"],
                self.lang["select_source_first"]
            )
            return
        
        IdSelectionDialog(self, self.src_bank_path, self.lang)
    
    def _open_hash_calculator_dialog(self) -> None:
        """Open hash calculator dialog"""
        HashCalculatorDialog(self, self.lang)

    def _exec_transfer(self) -> None:
        try:
            # Source soundbank path
            if not self.src_bank_path:
                raise ValueError(
                    self.lang["value_error_source_not_set"]
                )
            src_bank_dir = Path(self.src_bank_path).parent
            if not src_bank_dir.is_dir():
                raise ValueError(
                    self.lang["value_error_source_folder_not_exist"]
                )

            # Destination soundbank path
            if not self.dst_bank_path:
                raise ValueError(
                    self.lang["value_error_dest_not_set"]
                )
            dst_bank_dir = Path(self.dst_bank_path).parent
            if not dst_bank_dir.is_dir():
                raise ValueError(
                    self.lang["value_error_dest_folder_not_exist"]
                )

            # Get text from both boxes and split by lines
            src_wwise_lines = self.src_wwise_ids.get("1.0", tk.END).strip().split("\n")
            dst_wwise_lines = self.dst_wwise_ids.get("1.0", tk.END).strip().split("\n")

            # Filter out possible empty lines
            src_wwise_lines = [line for line in src_wwise_lines if line.strip()]
            dst_wwise_lines = [line for line in dst_wwise_lines if line.strip()]

            if not src_wwise_lines:
                raise ValueError(self.lang["value_error_no_lines"])
            if len(src_wwise_lines) != len(dst_wwise_lines):
                raise ValueError(
                    self.lang["value_error_line_mismatch"]
                )

            wwise_map = {
                src.strip(): dst.strip()
                for src, dst in zip(src_wwise_lines, dst_wwise_lines)
            }

            loading = LoadingDialog(
                self, self.lang["transferring_sounds"]
            )

            # Execute core logic in background thread
            def do_the_work():
                try:
                    copy_structure(
                        Soundbank.load(src_bank_dir),
                        Soundbank.load(dst_bank_dir),
                        wwise_map,
                    )
                except Exception as inner_exc:
                    traceback.print_exception(inner_exc)
                    self.after(
                        0,
                        lambda e=inner_exc: messagebox.showerror(
                            self.lang["error"], str(e)
                        ),
                    )
                else:
                    messagebox.showinfo(
                        self.lang["transfer_successful"],
                        self.lang["yay"],
                    )
                finally:
                    self.after(0, loading.close)

            thread = threading.Thread(target=do_the_work, daemon=True)
            thread.start()
        except Exception as e:
            traceback.print_exception(e)
            messagebox.showerror(
                self.lang["transfer_failed"], str(e)
            )


if __name__ == "__main__":
    app = SoundbankHelperGui()
    app.mainloop()