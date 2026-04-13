import tkinter as tk
from tkinter import ttk

from app.models import ProjectData
from app.services.autocomplete_service import (
    build_highlight_spans,
    find_character_matches,
    get_current_prefix,
)
from app.ui.autocomplete_popup import AutocompletePopup


class ChapterEditor(ttk.Frame):
    def __init__(self, parent, project: ProjectData | None, on_content_change, on_stats_change=None):
        super().__init__(parent, padding=10)

        self.project = project
        self.on_content_change_callback = on_content_change
        self.on_stats_change_callback = on_stats_change
        self.current_node_id = None
        self.prefix_start_index = None
        self.highlight_job = None
        self.last_highlight_signature: tuple[tuple[str, bool, str], ...] | None = None
        self.last_content_snapshot = ""

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.header = ttk.Frame(self, style="Card.TFrame", padding=14)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.header.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value="Selecciona un nodo")
        self.subtitle_var = tk.StringVar(value="Elige una historia, capítulo o escena para empezar a escribir.")
        self.stats_var = tk.StringVar(value="0 palabras · 0 caracteres")

        ttk.Label(self.header, textvariable=self.title_var, style="ProjectName.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.header, textvariable=self.subtitle_var, style="ProjectMeta.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )
        ttk.Label(self.header, textvariable=self.stats_var, style="ProjectMeta.TLabel").grid(
            row=0, column=1, rowspan=2, sticky="e"
        )

        self.editor_shell = tk.Frame(self, bg="#dbcdb7", bd=0, highlightthickness=0)
        self.editor_shell.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.editor_shell.grid_rowconfigure(0, weight=1)
        self.editor_shell.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(
            self.editor_shell,
            wrap="word",
            undo=True,
            padx=20,
            pady=18,
            relief="flat",
            bg="#fffdf9",
            fg="#2c241c",
            insertbackground="#2c5c79",
            selectbackground="#d8e8f1",
            selectforeground="#2c241c",
            font=("Georgia", 12),
            spacing1=2,
            spacing2=3,
            spacing3=6,
            insertwidth=2,
            highlightthickness=0,
            bd=0,
        )
        self.text.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=2, column=2, sticky="ns", padx=(8, 0))
        self.text.configure(yscrollcommand=scrollbar.set)

        self.popup = AutocompletePopup(self)

        self.text.bind("<KeyRelease>", self.on_key_release)
        self.text.bind("<Tab>", self.on_tab)
        self.text.bind("<Down>", self.on_down)
        self.text.bind("<Up>", self.on_up)
        self.text.bind("<Return>", self.on_return)
        self.text.bind("<Escape>", self.on_escape)
        self.text.bind("<Button-1>", self.on_click)

    def set_project(self, project: ProjectData | None):
        self.project = project
        self.last_highlight_signature = None
        self.refresh_character_highlights(force=True)

    def load_node(self, node):
        self.current_node_id = node.id
        self.title_var.set(node.title)
        self.subtitle_var.set("Escritura principal del nodo seleccionado.")
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", node.content)
        self.popup.hide()
        self.last_content_snapshot = ""
        self.refresh_character_highlights(force=True)
        self._notify_stats()

    def clear(self):
        self.current_node_id = None
        self.title_var.set("Selecciona un nodo")
        self.subtitle_var.set("Elige una historia, capítulo o escena para empezar a escribir.")
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.config(state="disabled")
        self.popup.hide()
        self.last_content_snapshot = ""
        self._notify_stats()

    def get_content(self):
        return self.text.get("1.0", tk.END).rstrip()

    def on_key_release(self, event=None):
        self.on_content_change_callback()
        self._notify_stats()
        self.schedule_highlight_refresh()

        ignored = {
            "Up",
            "Down",
            "Left",
            "Right",
            "Return",
            "Escape",
            "Tab",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
        }

        if event and event.keysym in ignored:
            return
        if not self.project:
            self.popup.hide()
            return

        cursor = self.text.index("insert")
        line_start = self.text.index(f"{cursor} linestart")
        text_before_cursor = self.text.get(line_start, cursor)

        prefix = get_current_prefix(text_before_cursor)
        if not prefix or len(prefix) < 2:
            self.popup.hide()
            return

        start_col = len(text_before_cursor) - len(prefix)
        self.prefix_start_index = f"{cursor.split('.')[0]}.{start_col}"

        matches = find_character_matches(self.project, prefix)
        if not matches:
            self.popup.hide()
            return

        bbox = self.text.bbox(cursor)
        if not bbox:
            self.popup.hide()
            return

        x, y, _width, height = bbox
        abs_x = self.text.winfo_rootx() + x
        abs_y = self.text.winfo_rooty() + y + height
        self.popup.show(matches, abs_x, abs_y)

    def insert_selected(self):
        selected = self.popup.get_selected()
        if not selected or not self.prefix_start_index:
            return False

        self.text.delete(self.prefix_start_index, "insert")
        self.text.insert("insert", selected)
        self.popup.hide()
        self.on_content_change_callback()
        self._notify_stats()
        self.schedule_highlight_refresh()
        return True

    def on_tab(self, _event=None):
        if self.popup.is_visible():
            self.insert_selected()
            return "break"
        return None

    def on_down(self, _event=None):
        if self.popup.is_visible():
            self.popup.select_next()
            return "break"
        return None

    def on_up(self, _event=None):
        if self.popup.is_visible():
            self.popup.select_previous()
            return "break"
        return None

    def on_return(self, _event=None):
        if self.popup.is_visible():
            self.insert_selected()
            return "break"
        return None

    def on_escape(self, _event=None):
        if self.popup.is_visible():
            self.popup.hide()
            return "break"
        return None

    def on_click(self, _event=None):
        self.popup.hide()

    def set_enabled(self, enabled: bool):
        self.text.config(state="normal" if enabled else "disabled")

    def schedule_highlight_refresh(self):
        if self.highlight_job:
            self.after_cancel(self.highlight_job)
        self.highlight_job = self.after(180, self.refresh_character_highlights)

    def refresh_character_highlights(self, force: bool = False):
        if self.highlight_job:
            self.after_cancel(self.highlight_job)
            self.highlight_job = None

        content = self.text.get("1.0", "end-1c")
        signature = self._build_character_signature()
        if not force and content == self.last_content_snapshot and signature == self.last_highlight_signature:
            return

        for tag in self.text.tag_names():
            if tag.startswith("char_"):
                self.text.tag_remove(tag, "1.0", "end")

        if not self.project:
            self.last_content_snapshot = content
            self.last_highlight_signature = signature
            return

        for tag_name, config in build_highlight_spans(self.project, content).items():
            self.text.tag_config(tag_name, background=config["color"])
            for start_idx, end_idx in config["ranges"]:
                start = f"1.0+{start_idx}c"
                end = f"1.0+{end_idx}c"
                self.text.tag_add(tag_name, start, end)

        self.last_content_snapshot = content
        self.last_highlight_signature = signature

    def _build_character_signature(self):
        if not self.project:
            return ()
        return tuple(
            sorted(
                (
                    character.name,
                    character.highlight_enabled,
                    character.highlight_color,
                )
                for character in self.project.characters.values()
            )
        )

    def _notify_stats(self):
        content = self.text.get("1.0", "end-1c")
        words = len([token for token in content.split() if token])
        characters = len(content)
        self.stats_var.set(f"{words} palabras · {characters} caracteres")
        if self.on_stats_change_callback:
            self.on_stats_change_callback(words, characters)
