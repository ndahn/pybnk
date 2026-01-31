#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import traceback
import threading

from pybnk import Soundbank
from pybnk.gui.localization import Localization, English, Chinese


class ToolTip:
    def __init__(self, widget, text_key: str, lang: Localization):
        self.widget = widget
        self.text_key = text_key
        self.lang: Localization = lang
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

    def update_text(self):
        # The text is fetched dynamically in show(), so no action is needed here
        pass


class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message: str = "Processing..."):
        super().__init__(parent)

        self.title("Please Wait")
        self.transient(parent)
        self.grab_set()

        self.overrideredirect(True)
        self.geometry("300x100")

        frame = tk.Frame(self, relief="solid", borderwidth=2, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(frame, text=message, bg="white", font=("TkDefaultFont", 10)).pack(
            pady=20
        )

        self.progress = ttk.Progressbar(frame, mode="indeterminate", length=250)
        self.progress.pack(pady=10)
        self.progress.start(10)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def close(self):
        self.progress.stop()
        self.destroy()


class CreateSoundDialog(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- I18N and Widget Storage ---
        self.lang: Localization = English()
        self.widgets = {}
        self.tooltips = []

        self.title(self.lang["create_sound_title"])
        self.geometry("600x600")

        self.soundbank = None
        self.soundbank_path: str = ""
        self.wem_file_path: str = ""

        # Variables
        self.soundtype_var = tk.StringVar()
        self.sound_id_var = tk.StringVar()
        self.actor_mixer_var = tk.StringVar()
        self.playback_type_var = tk.StringVar(value="Embedded")
        self.warning_var = tk.StringVar()

        # Sound type options
        self.soundtype_options = {
            "s": "SFX",
            "v": "Voice",
            "c": "Character",
            "m": "Music",
            "a": "Ambience",
            "u": "UI",
            "f": "Foley",
            "d": "Dialogue",
            "w": "Walla",
            "e": "Environment",
        }

        # Playback type options
        self.playback_options = ["Embedded", "StreamingPrefetch"]

        # Actor mixer objects (populated when soundbank is loaded)
        self.actor_mixer_objects = []

        # Create UI
        self._create_widgets()
        self._update_ui_text()
        self._setup_validation()

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

        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for alignment
        main_frame.columnconfigure(0, weight=0)  # Help icon
        main_frame.columnconfigure(1, weight=0)  # Label
        main_frame.columnconfigure(2, weight=1)  # Input widget
        main_frame.columnconfigure(3, weight=0)  # Extra (button/display)

        row = 0

        # --- Soundbank file selection ---
        help_soundbank = ttk.Label(
            main_frame, text="ℹ", foreground="blue", cursor="hand2"
        )
        help_soundbank.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_soundbank, "soundbank_tooltip", self.lang))

        self.widgets["soundbank_label"] = ttk.Label(main_frame)
        self.widgets["soundbank_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.soundbank_display = ttk.Label(
            main_frame,
            text=self.lang["no_file_selected"],
            foreground="gray",
        )
        self.soundbank_display.grid(row=row, column=2, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.widgets["browse_soundbank_button"] = ttk.Button(
            main_frame, command=self._browse_soundbank
        )
        self.widgets["browse_soundbank_button"].grid(row=row, column=3, sticky=tk.W, pady=(0, 15))

        row += 1

        # --- Sound Type ---
        help_type = ttk.Label(main_frame, text="ℹ", foreground="blue", cursor="hand2")
        help_type.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_type, "soundtype_tooltip", self.lang))

        self.widgets["soundtype_label"] = ttk.Label(main_frame)
        self.widgets["soundtype_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        # Create combobox with sound types
        soundtype_values = [
            f"{key} - {value}" for key, value in self.soundtype_options.items()
        ]
        self.soundtype_combo = ttk.Combobox(
            main_frame, textvariable=self.soundtype_var, values=soundtype_values, width=30
        )
        self.soundtype_combo.grid(row=row, column=2, columnspan=2, sticky=tk.W, pady=(0, 15))
        self.soundtype_combo.bind("<<ComboboxSelected>>", self._on_soundtype_change)

        row += 1

        # --- Sound ID ---
        help_id = ttk.Label(main_frame, text="ℹ", foreground="blue", cursor="hand2")
        help_id.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_id, "sound_id_tooltip", self.lang))

        self.widgets["sound_id_label"] = ttk.Label(main_frame)
        self.widgets["sound_id_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.sound_id_entry = ttk.Entry(
            main_frame, textvariable=self.sound_id_var, width=30
        )
        self.sound_id_entry.grid(row=row, column=2, columnspan=2, sticky=tk.W, pady=(0, 15))

        row += 1

        # --- ActorMixer ---
        help_mixer = ttk.Label(main_frame, text="ℹ", foreground="blue", cursor="hand2")
        help_mixer.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_mixer, "actor_mixer_tooltip", self.lang))

        self.widgets["actor_mixer_label"] = ttk.Label(main_frame)
        self.widgets["actor_mixer_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.actor_mixer_combo = ttk.Combobox(
            main_frame,
            textvariable=self.actor_mixer_var,
            state="readonly",
            width=30,
        )
        self.actor_mixer_combo.grid(row=row, column=2, columnspan=2, sticky=tk.W, pady=(0, 15))

        row += 1

        # --- Playback Type ---
        help_playback = ttk.Label(
            main_frame, text="ℹ", foreground="blue", cursor="hand2"
        )
        help_playback.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_playback, "playback_type_tooltip", self.lang))

        self.widgets["playback_type_label"] = ttk.Label(main_frame)
        self.widgets["playback_type_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        # Create radio buttons for playback types
        playback_buttons_frame = ttk.Frame(main_frame)
        playback_buttons_frame.grid(row=row, column=2, columnspan=2, sticky=tk.W, pady=(0, 15))

        for playback in self.playback_options:
            ttk.Radiobutton(
                playback_buttons_frame,
                text=playback,
                variable=self.playback_type_var,
                value=playback,
            ).pack(side=tk.LEFT, padx=(0, 15))

        row += 1

        # --- WEM File ---
        help_wem = ttk.Label(main_frame, text="ℹ", foreground="blue", cursor="hand2")
        help_wem.grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 15))
        self.tooltips.append(ToolTip(help_wem, "wem_file_tooltip", self.lang))

        self.widgets["wem_file_label"] = ttk.Label(main_frame)
        self.widgets["wem_file_label"].grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.wem_display = ttk.Label(
            main_frame,
            text=self.lang["no_file_selected"],
            foreground="gray",
        )
        self.wem_display.grid(row=row, column=2, sticky=tk.W, padx=(0, 10), pady=(0, 15))

        self.widgets["browse_wem_button"] = ttk.Button(
            main_frame, command=self._browse_wem
        )
        self.widgets["browse_wem_button"].grid(row=row, column=3, sticky=tk.W, pady=(0, 15))

        row += 1

        # --- Warning label ---
        self.warning_label = ttk.Label(
            main_frame,
            textvariable=self.warning_var,
            foreground="red",
            wraplength=550,
            font=("Arial", 9),
        )
        self.warning_label.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(15, 0))

        row += 1

        # --- Separator ---
        separator = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        separator.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=10, pady=15)

        row += 1

        # --- Explanation text ---
        self.info_text = tk.Text(main_frame, height=4, wrap=tk.WORD)
        self.info_text.config(state=tk.DISABLED)
        self.info_text.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))

        row += 1

        # --- Generate button ---
        self.widgets["generate_button"] = ttk.Button(
            main_frame, command=self._generate, state="disabled"
        )
        self.widgets["generate_button"].grid(row=row, column=0, columnspan=4, pady=10)

    def _change_language(self, event=None):
        selected_language = self.lang_combo.get()
        if selected_language == "English":
            self.lang = English()
        elif selected_language == "中文":
            self.lang = Chinese()
        else:
            raise ValueError(f"Unknown translation {selected_language}")

        self._update_ui_text()

    def _update_ui_text(self):
        self.title(self.lang["create_sound_title"])

        # Update all labeled widgets
        self.widgets["soundbank_label"].config(text=self.lang["soundbank_file_label"])
        self.widgets["browse_soundbank_button"].config(text=self.lang["browse"])
        self.widgets["soundtype_label"].config(text=self.lang["soundtype_label"])
        self.widgets["sound_id_label"].config(text=self.lang["sound_id_label"])
        self.widgets["actor_mixer_label"].config(text=self.lang["actor_mixer_label"])
        self.widgets["playback_type_label"].config(
            text=self.lang["playback_type_label"]
        )
        self.widgets["wem_file_label"].config(text=self.lang["wem_file_label"])
        self.widgets["browse_wem_button"].config(text=self.lang["browse"])
        self.widgets["generate_button"].config(text=self.lang["generate_button"])

        # Update explanation text
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", self.lang["create_sound_info_text"])
        self.info_text.config(state=tk.DISABLED)

        # Update tooltips
        for tooltip in self.tooltips:
            tooltip.update_text()

        # Update display labels if no file is selected
        if not self.soundbank_path:
            self.soundbank_display.config(text=self.lang["no_file_selected"])
        if not self.wem_file_path:
            self.wem_display.config(text=self.lang["no_file_selected"])

    def _setup_validation(self) -> None:
        """Setup real-time validation for ID field"""
        self.sound_id_var.trace_add("write", self._validate_inputs)
        self.soundtype_var.trace_add("write", self._validate_inputs)
        self.actor_mixer_var.trace_add("write", self._validate_inputs)
        self.playback_type_var.trace_add("write", self._validate_inputs)

    def _browse_soundbank(self) -> None:
        """Open file dialog to select soundbank.json"""
        path = filedialog.askopenfilename(
            title=self.lang["select_soundbank"],
            filetypes=[
                (self.lang["json_files"], "soundbank.json"),
                (self.lang["all_files"], "*.*"),
            ],
        )

        if path:
            print(f"Selected soundbank: {path}")
            self.soundbank_path = path
            self.soundbank_display.config(
                text=Path(path).parent.name, foreground="black"
            )
            self._load_soundbank(path)

    def _load_soundbank(self, filepath: str) -> None:
        """Load the soundbank and populate ActorMixer options"""
        try:
            loading = LoadingDialog(self, self.lang["loading_soundbank"])

            def do_load():
                try:
                    self.soundbank = Soundbank.load(filepath)

                    # Query for ActorMixers
                    actor_mixers = self.soundbank.query({"type": "ActorMixer"})

                    loading.close()

                    if actor_mixers:
                        self.actor_mixer_objects = actor_mixers
                        # Extract names or IDs for the dropdown
                        mixer_names = [str(am) for am in actor_mixers]
                        self.actor_mixer_combo["values"] = mixer_names
                        if mixer_names:
                            self.actor_mixer_combo.current(0)
                    else:
                        self.actor_mixer_combo["values"] = []
                        self.warning_var.set(self.lang["no_actor_mixers_warning"])

                    self._validate_inputs()

                except Exception as inner_exc:
                    traceback.print_exception(inner_exc)
                    loading.close()
                    self.after(
                        0,
                        lambda e=inner_exc: messagebox.showerror(
                            self.lang["error"], str(e)
                        ),
                    )
                    self.soundbank = None

            thread = threading.Thread(target=do_load, daemon=True)
            thread.start()

        except Exception as e:
            traceback.print_exception(e)
            messagebox.showerror(self.lang["error"], str(e))
            self.soundbank = None

    def _browse_wem(self) -> None:
        """Open file dialog to select .wem file"""
        path = filedialog.askopenfilename(
            title=self.lang["select_wem_file"],
            filetypes=[
                (self.lang["wem_files"], "*.wem"),
                (self.lang["all_files"], "*.*"),
            ],
        )

        if path:
            print(f"Selected WEM file: {path}")
            self.wem_file_path = path
            self.wem_display.config(text=Path(path).name, foreground="black")
            self._validate_inputs()

    def _on_soundtype_change(self, event=None) -> None:
        """Handle soundtype selection change"""
        self._validate_inputs()

    def _validate_inputs(self, *args) -> None:
        """Validate all inputs and update warning/button state"""
        warnings = []

        # Validate ID
        id_value = self.sound_id_var.get()
        if id_value:
            if not id_value.isdigit():
                warnings.append(self.lang["warning_id_numeric"])
            elif len(id_value) < 4:
                warnings.append(self.lang["warning_id_too_short"])
            elif len(id_value) > 10:
                warnings.append(self.lang["warning_id_too_long"])
            elif self.soundbank and len(id_value) >= 4:
                # Check for duplicate ID
                try:
                    existing = self.soundbank.query({"id": id_value})
                    if existing:
                        warnings.append(
                            self.lang["warning_id_exists"].format(id=id_value)
                        )
                except Exception:
                    pass

        # Update warning display
        if warnings:
            self.warning_var.set(" | ".join(warnings))
        else:
            self.warning_var.set("")

        # Update generate button state
        self._update_generate_button_state()

    def _update_generate_button_state(self) -> None:
        """Enable/disable generate button based on form completion"""
        id_value = self.sound_id_var.get()
        soundtype_value = self.soundtype_var.get()

        # Extract just the character key from the selection (e.g., "s - SFX" -> "s")
        soundtype_key = soundtype_value.split(" - ")[0] if soundtype_value else ""

        if (
            self.soundbank
            and soundtype_key
            and id_value
            and len(id_value) >= 4
            and len(id_value) <= 10
            and id_value.isdigit()
            and self.actor_mixer_var.get()
            and self.playback_type_var.get()
            and self.wem_file_path
            and Path(self.wem_file_path).exists()
        ):
            self.widgets["generate_button"]["state"] = "normal"
        else:
            self.widgets["generate_button"]["state"] = "disabled"

    def _generate(self) -> None:
        """Collect all data and call the generation function"""
        try:
            # Final validation
            warnings = []

            if not self.soundbank:
                warnings.append(self.lang["error_soundbank_not_loaded"])

            soundtype_value = self.soundtype_var.get()
            soundtype_key = soundtype_value.split(" - ")[0] if soundtype_value else ""
            if not soundtype_key:
                warnings.append(self.lang["error_no_soundtype"])

            id_value = self.sound_id_var.get()
            if not id_value or not id_value.isdigit():
                warnings.append(self.lang["error_invalid_id"])
            elif len(id_value) < 4 or len(id_value) > 10:
                warnings.append(self.lang["error_id_length"])

            if not self.actor_mixer_var.get():
                warnings.append(self.lang["error_no_actor_mixer"])

            if not self.playback_type_var.get():
                warnings.append(self.lang["error_no_playback_type"])

            if not self.wem_file_path or not Path(self.wem_file_path).exists():
                warnings.append(self.lang["error_no_wem_file"])

            if warnings:
                self.warning_var.set("; ".join(warnings))
                return

            # Get the actual ActorMixer object
            mixer_index = self.actor_mixer_combo.current()
            actor_mixer_obj = (
                self.actor_mixer_objects[mixer_index]
                if mixer_index >= 0
                else None
            )

            # Collect all data
            data = {
                "soundbank": self.soundbank,
                "soundtype": soundtype_key,
                "sound_id": id_value,
                "actor_mixer": actor_mixer_obj,
                "playback_type": self.playback_type_var.get(),
                "wem_file": self.wem_file_path,
            }

            loading = LoadingDialog(self, self.lang["generating_sound"])

            # Execute generation in background thread
            def do_generate():
                try:
                    # TODO: Call your actual generation function here
                    # Example: your_generation_function(data)
                    
                    # Placeholder for demonstration
                    import time
                    time.sleep(1)  # Simulate work
                    
                    loading.close()
                    self.after(
                        0,
                        lambda: messagebox.showinfo(
                            self.lang["generation_successful"],
                            self.lang["generation_complete_message"].format(
                                soundtype=soundtype_key,
                                id=id_value,
                                mixer=self.actor_mixer_var.get(),
                                playback=data["playback_type"],
                                wem=Path(data["wem_file"]).name,
                            ),
                        ),
                    )

                except Exception as inner_exc:
                    traceback.print_exception(inner_exc)
                    loading.close()
                    self.after(
                        0,
                        lambda e=inner_exc: messagebox.showerror(
                            self.lang["error"], str(e)
                        ),
                    )

            thread = threading.Thread(target=do_generate, daemon=True)
            thread.start()

        except Exception as e:
            traceback.print_exception(e)
            messagebox.showerror(self.lang["error"], str(e))


if __name__ == "__main__":
    app = CreateSoundDialog()
    app.mainloop()