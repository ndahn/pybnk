import tkinter as tk
from tkinter import ttk


class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message: str = "Processing...", title="Please Wait"):
        super().__init__(parent)

        self.title(title)
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
