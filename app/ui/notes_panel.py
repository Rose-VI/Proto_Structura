import tkinter as tk
from tkinter import ttk


class NotesPanel(ttk.Frame):
    def __init__(self, parent, on_notes_change):
        super().__init__(parent, padding=10)

        self.on_notes_change_callback = on_notes_change
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text="Notas del nodo seleccionado",
            style="PanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.shell = tk.Frame(self, bg="#dbcdb7", bd=0, highlightthickness=0)
        self.shell.grid(row=1, column=0, sticky="nsew")
        self.shell.grid_rowconfigure(0, weight=1)
        self.shell.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(
            self.shell,
            wrap="word",
            undo=True,
            padx=16,
            pady=16,
            relief="flat",
            bg="#fffdf9",
            fg="#2c241c",
            insertbackground="#2c5c79",
            selectbackground="#d8e8f1",
            selectforeground="#2c241c",
            font=("Georgia", 11),
            spacing1=2,
            spacing2=3,
            spacing3=5,
            highlightthickness=0,
            bd=0,
        )
        self.text.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.text.bind("<KeyRelease>", lambda _event: self.on_notes_change_callback())

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(8, 0))
        self.text.configure(yscrollcommand=scrollbar.set)

    def load_notes(self, notes: str):
        previous_state = self.text.cget("state")
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", notes)
        self.text.config(state=previous_state)

    def clear(self):
        previous_state = self.text.cget("state")
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.config(state=previous_state)

    def get_notes(self):
        return self.text.get("1.0", tk.END).rstrip()

    def set_enabled(self, enabled: bool):
        self.text.config(state="normal" if enabled else "disabled")
