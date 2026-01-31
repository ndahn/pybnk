import tkinter as tk

from pybnk.gui.localization import Localization


class ToolTip:
    def __init__(self, widget, text_key: str, lang):
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

    # Method for updating tooltip text when language changes
    def update_text(self):
        # The text is fetched dynamically in show(), so no action is needed here
        # unless we want to pre-fetch it. For simplicity, we'll let it be.
        pass
