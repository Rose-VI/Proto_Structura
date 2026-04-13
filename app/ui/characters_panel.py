import tkinter as tk
from tkinter import colorchooser, ttk


class CharactersPanel(ttk.Frame):
    def __init__(self, parent, on_select, on_highlight_change=None, on_color_change=None):
        super().__init__(parent, padding=10)

        self.on_select_callback = on_select
        self.on_highlight_change_callback = on_highlight_change
        self.on_color_change_callback = on_color_change
        self.current_color = "#ffd54f"

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        ttk.Label(toolbar, text="Personajes", style="PanelTitle.TLabel").pack(side="left", padx=(0, 8))

        self.btn_new = ttk.Button(toolbar, text="Nuevo")
        self.btn_new.pack(side="left", padx=3)

        self.btn_rename = ttk.Button(toolbar, text="Renombrar")
        self.btn_rename.pack(side="left", padx=3)

        self.btn_delete = ttk.Button(toolbar, text="Eliminar")
        self.btn_delete.pack(side="left", padx=3)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", padx=8, fill="y")

        self.highlight_var = tk.BooleanVar(value=True)
        self.chk_highlight = ttk.Checkbutton(
            toolbar,
            text="Resaltar",
            variable=self.highlight_var,
            command=self.on_highlight_toggle,
        )
        self.chk_highlight.pack(side="left", padx=3)

        self.btn_color = tk.Button(
            toolbar,
            text="  ",
            width=2,
            command=self.choose_color,
            relief="flat",
            bg=self.current_color,
            activebackground=self.current_color,
        )
        self.btn_color.pack(side="left", padx=3)

        self.listbox = tk.Listbox(
            self,
            exportselection=False,
            width=22,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg="#fcfaf6",
            fg="#2c241c",
            selectbackground="#d8e8f1",
            selectforeground="#2c241c",
        )
        self.listbox.grid(row=1, column=0, sticky="nsw", padx=(0, 10))
        self.listbox.bind("<<ListboxSelect>>", self.on_select_callback)

        self.editor_shell = tk.Frame(self, bg="#dbcdb7", bd=0, highlightthickness=0)
        self.editor_shell.grid(row=1, column=1, sticky="nsew")
        self.editor_shell.grid_rowconfigure(0, weight=1)
        self.editor_shell.grid_columnconfigure(0, weight=1)

        self.description = tk.Text(
            self.editor_shell,
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
        self.description.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.description.yview)
        scrollbar.grid(row=1, column=2, sticky="ns", padx=(8, 0))
        self.description.configure(yscrollcommand=scrollbar.set)

    def set_character_names(self, names):
        selected = self.get_selected_name()
        self.listbox.delete(0, tk.END)
        selected_index = None
        for index, name in enumerate(names):
            self.listbox.insert(tk.END, name)
            if name == selected:
                selected_index = index

        if selected_index is not None:
            self.listbox.selection_set(selected_index)
            self.listbox.see(selected_index)

    def get_selected_name(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])

    def select_name(self, name: str | None):
        self.listbox.selection_clear(0, tk.END)
        if not name:
            return
        for index in range(self.listbox.size()):
            if self.listbox.get(index) == name:
                self.listbox.selection_set(index)
                self.listbox.see(index)
                return

    def load_description(self, text):
        previous_state = self.description.cget("state")
        self.description.config(state="normal")
        self.description.delete("1.0", tk.END)
        self.description.insert("1.0", text)
        self.description.config(state=previous_state)

    def get_description(self):
        return self.description.get("1.0", tk.END).rstrip()

    def clear_description(self):
        previous_state = self.description.cget("state")
        self.description.config(state="normal")
        self.description.delete("1.0", tk.END)
        self.description.config(state=previous_state)

    def on_highlight_toggle(self):
        if self.on_highlight_change_callback:
            self.on_highlight_change_callback()

    def choose_color(self):
        color = colorchooser.askcolor(
            title="Elegir color",
            initialcolor=self.current_color,
        )[1]
        if color:
            self.set_highlight_color(color)
            if self.on_color_change_callback:
                self.on_color_change_callback()

    def set_highlight_enabled(self, enabled: bool):
        self.highlight_var.set(enabled)

    def get_highlight_enabled(self) -> bool:
        return self.highlight_var.get()

    def set_highlight_color(self, color: str):
        if color:
            self.current_color = color
            self.btn_color.config(bg=color, activebackground=color)

    def get_highlight_color(self) -> str:
        return self.current_color

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for widget in (
            self.btn_new,
            self.btn_rename,
            self.btn_delete,
            self.chk_highlight,
        ):
            widget.config(state=state)
        self.description.config(state=state)
        self.listbox.config(state=state)
        self.btn_color.config(state=state)
