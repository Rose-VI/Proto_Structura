from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Literal

from app.paths import ensure_user_data_dir
from app.controllers.project_controller import ProjectController
from app.project_library import ProjectLibrary, ProjectRecord, describe_project
from app.repository import ProjectValidationError
from app.services import chapter_service, character_service
from app.services.chapter_service import ChapterStructureError
from app.services.export_service import export_story as export_story_service
from app.ui.chapter_editor import ChapterEditor
from app.ui.chapter_tree import ChapterTree
from app.ui.characters_panel import CharactersPanel
from app.ui.notes_panel import NotesPanel


DATA_DIR = ensure_user_data_dir()
APP_TITLE = "Structura"
MSG_SELECT_STORY = "Selecciona una historia para agregar un capítulo."
MSG_SELECT_CHAPTER = "Selecciona un capítulo para agregar una escena."
MSG_SELECT_NODE = "Selecciona un nodo primero."
MSG_SELECT_CHARACTER = "Selecciona un personaje."
MSG_OPEN_PROJECT_FIRST = "Primero crea o abre un proyecto para usar esta acción."
MSG_SAVED = "Proyecto guardado correctamente."

THEME = {
    "bg": "#f3efe7",
    "surface": "#fcfaf6",
    "surface_alt": "#f6f1e8",
    "border": "#dbcdb7",
    "accent": "#2c5c79",
    "accent_soft": "#d8e8f1",
    "warm": "#b85c38",
    "text": "#2c241c",
    "muted": "#74665a",
    "disabled": "#b7aa9a",
    "editor_bg": "#fffdf9",
}

HOME_COMPACT_WIDTH = 1120
EDITOR_COMPACT_WIDTH = 1160
EDITOR_TIGHT_WIDTH = 930


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1420x880")
        self.root.minsize(880, 620)

        self.controller = ProjectController()
        self.project_library = ProjectLibrary(DATA_DIR)
        self.project_records: list[ProjectRecord] = []
        self.selected_project_path: str | None = None
        self.layout_mode: Literal["wide", "compact"] = "wide"
        self.left_panel_user_visible = True
        self.right_panel_user_visible = True
        self.left_panel_auto_hidden = False
        self.right_panel_auto_hidden = False

        self.status_project = tk.StringVar()
        self.status_dirty = tk.StringVar()
        self.status_selection = tk.StringVar()
        self.status_stats = tk.StringVar(value="0 palabras · 0 caracteres")
        self.library_hint = tk.StringVar()

        self._configure_styles()
        self.build_ui()
        self.show_home()
        self.root.bind("<Configure>", self.update_responsive_layout)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.root.configure(bg=THEME["bg"])
        style.configure(".", background=THEME["bg"], foreground=THEME["text"])
        style.configure("TFrame", background=THEME["bg"])
        style.configure("HomeCard.TFrame", background=THEME["surface"])
        style.configure("Card.TFrame", background=THEME["surface"])
        style.configure("CardAlt.TFrame", background=THEME["surface_alt"])
        style.configure("Toolbar.TFrame", background=THEME["bg"])
        style.configure("Status.TFrame", background=THEME["surface_alt"])
        style.configure(
            "HomeTitle.TLabel",
            background=THEME["bg"],
            foreground=THEME["accent"],
            font=("Georgia", 26, "bold"),
        )
        style.configure(
            "HomeSubtitle.TLabel",
            background=THEME["bg"],
            foreground=THEME["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "PanelTitle.TLabel",
            background=THEME["bg"],
            foreground=THEME["accent"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "PanelTitleCard.TLabel",
            background=THEME["surface"],
            foreground=THEME["accent"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "GroupTitle.TLabel",
            background=THEME["bg"],
            foreground=THEME["warm"],
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Status.TLabel",
            background=THEME["surface_alt"],
            foreground=THEME["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "ProjectName.TLabel",
            background=THEME["surface"],
            foreground=THEME["text"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "ProjectMeta.TLabel",
            background=THEME["surface"],
            foreground=THEME["muted"],
            font=("Segoe UI", 9),
        )
        style.configure("Primary.TButton", padding=(12, 7))
        style.configure(
            "Hero.TButton",
            padding=(18, 12),
            background=THEME["accent"],
            foreground="#ffffff",
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Hero.TButton",
            background=[("active", "#22475f")],
            foreground=[("disabled", "#f1ebe4")],
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["accent_soft"])],
            foreground=[("selected", THEME["text"])],
        )
        style.configure(
            "Treeview",
            rowheight=30,
            fieldbackground=THEME["surface"],
            background=THEME["surface"],
            foreground=THEME["text"],
        )
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            padding=(12, 8),
            background=THEME["surface_alt"],
            foreground=THEME["muted"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["surface"])],
            foreground=[("selected", THEME["accent"])],
        )

    def build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.container = ttk.Frame(self.root, padding=10)
        self.container.grid(sticky="nsew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.home_view = ttk.Frame(self.container)
        self.home_view.grid(row=0, column=0, sticky="nsew")
        self.editor_view = ttk.Frame(self.container)
        self.editor_view.grid(row=0, column=0, sticky="nsew")
        self._build_home_view()
        self._build_editor_view()

    def _build_home_view(self):
        self.home_view.rowconfigure(1, weight=1)
        self.home_view.columnconfigure(0, weight=3)
        self.home_view.columnconfigure(1, weight=2)
        hero = ttk.Frame(self.home_view)
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ttk.Label(hero, text="Tus proyectos", style="HomeTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hero, text="Abre rápido tus historias, fija favoritas e importa un JSON si no aparece en la lista.", style="HomeSubtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        library_card = ttk.Frame(self.home_view, style="HomeCard.TFrame", padding=14)
        library_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        library_card.rowconfigure(1, weight=1)
        library_card.columnconfigure(0, weight=1)
        header = ttk.Frame(library_card, style="HomeCard.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Lista de proyectos", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.pin_button = ttk.Button(header, text="Fijar / quitar", command=self.toggle_selected_pin)
        self.pin_button.grid(row=0, column=1, sticky="e")

        self.project_list = tk.Listbox(library_card, activestyle="none", font=("Segoe UI", 11), relief="flat", bd=0, exportselection=False)
        self.project_list.grid(row=1, column=0, sticky="nsew")
        self.project_list.bind("<<ListboxSelect>>", self.on_project_record_select)
        self.project_list.bind("<Double-Button-1>", lambda _e: self.open_selected_project())
        list_scroll = ttk.Scrollbar(library_card, orient="vertical", command=self.project_list.yview)
        list_scroll.grid(row=1, column=1, sticky="ns")
        self.project_list.configure(yscrollcommand=list_scroll.set)
        self.project_list.config(
            highlightthickness=0,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectbackground=THEME["accent_soft"],
            selectforeground=THEME["text"],
        )

        self.project_preview = ttk.Frame(library_card, style="CardAlt.TFrame", padding=12)
        self.project_preview.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.project_preview.columnconfigure(0, weight=1)
        self.preview_title = ttk.Label(self.project_preview, text="Selecciona un proyecto", style="ProjectName.TLabel")
        self.preview_title.grid(row=0, column=0, sticky="w")
        self.preview_subtitle = ttk.Label(self.project_preview, text="", style="ProjectMeta.TLabel")
        self.preview_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.preview_summary = ttk.Label(self.project_preview, text="", style="ProjectMeta.TLabel")
        self.preview_summary.grid(row=2, column=0, sticky="w", pady=(4, 0))

        actions = ttk.Frame(self.home_view, style="HomeCard.TFrame", padding=20)
        actions.grid(row=1, column=1, sticky="nsew")
        actions.columnconfigure(0, weight=1)
        actions.rowconfigure(4, weight=1)
        self.library_card = library_card
        self.actions_card = actions
        ttk.Label(actions, text="Acciones rápidas", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(actions, text="Empieza una historia nueva o importa un proyecto que no esté registrado todavía.", style="HomeSubtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 18))
        ttk.Button(actions, text="Crear una historia nueva", command=self.new_project, style="Hero.TButton").grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(actions, text="Importar JSON", command=self.import_project_json, style="Hero.TButton").grid(row=3, column=0, sticky="ew", pady=(0, 16))
        ttk.Button(actions, text="Abrir proyecto seleccionado", command=self.open_selected_project, style="Primary.TButton").grid(row=4, column=0, sticky="ew")
        ttk.Label(actions, textvariable=self.library_hint, style="ProjectMeta.TLabel", wraplength=320).grid(row=5, column=0, sticky="sw", pady=(18, 0))

    def _build_editor_view(self):
        self.editor_view.rowconfigure(1, weight=1)
        self.editor_view.columnconfigure(0, weight=1)
        self.toolbar = ttk.Frame(self.editor_view, style="Toolbar.TFrame")
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_toolbar()
        self.main_pane = tk.PanedWindow(
            self.editor_view,
            orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED,
            bd=0,
            bg=THEME["bg"],
            sashwidth=8,
            relief="flat",
        )
        self.main_pane.grid(row=1, column=0, sticky="nsew")
        self.chapter_tree = ChapterTree(self.main_pane, self.on_tree_select)
        self.chapter_tree.bind_context_menu(self.on_tree_context_menu)
        self.chapter_editor = ChapterEditor(self.main_pane, self.controller.project, self.on_content_change, self.on_editor_stats_change)
        self.right_tabs = ttk.Notebook(self.main_pane)
        self.notes_panel = NotesPanel(self.right_tabs, self.on_notes_change)
        self.characters_panel = CharactersPanel(self.right_tabs, self.on_character_select, self.on_character_highlight_change, self.on_character_color_change)
        self.right_tabs.add(self.notes_panel, text="Notas")
        self.right_tabs.add(self.characters_panel, text="Personajes")
        self.characters_panel.btn_new.config(command=self.add_character)
        self.characters_panel.btn_rename.config(command=self.rename_character)
        self.characters_panel.btn_delete.config(command=self.delete_character)
        self.main_pane.add(self.chapter_tree, minsize=180, stretch="never")
        self.main_pane.add(self.chapter_editor, minsize=420, stretch="always")
        self.main_pane.add(self.right_tabs, minsize=220, stretch="never")
        self.status_bar = ttk.Frame(self.editor_view, style="Status.TFrame", padding=(10, 6))
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for column in range(4):
            self.status_bar.columnconfigure(column, weight=1 if column == 2 else 0)
        self.status_path_label = ttk.Label(self.status_bar, textvariable=self.status_project, style="Status.TLabel")
        self.status_path_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(self.status_bar, textvariable=self.status_dirty, style="Status.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 10))
        ttk.Label(self.status_bar, textvariable=self.status_selection, style="Status.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(self.status_bar, textvariable=self.status_stats, style="Status.TLabel").grid(row=0, column=3, sticky="e")
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Nueva historia", command=self.add_story)
        self.tree_menu.add_command(label="Nuevo capítulo", command=self.add_chapter)
        self.tree_menu.add_command(label="Nueva escena", command=self.add_section)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Renombrar", command=self.rename_node)
        self.tree_menu.add_command(label="Eliminar", command=self.delete_node)

    def _build_toolbar(self):
        groups = ttk.Frame(self.toolbar)
        groups.grid(sticky="ew")
        self._toolbar_group(groups, 0, "Inicio", [("Volver al inicio", self.close_project)])
        self._toolbar_group(groups, 1, "Proyecto", [("Nuevo", self.new_project), ("Abrir", self.open_project), ("Guardar", self.save), ("Guardar como", self.save_as)])
        self._toolbar_group(groups, 2, "Estructura", [("Nueva historia", self.add_story), ("Nuevo capítulo", self.add_chapter), ("Nueva escena", self.add_section), ("Renombrar", self.rename_node), ("Eliminar", self.delete_node)])
        self._toolbar_group(groups, 3, "Paneles", [("Capítulos", self.toggle_left_panel), ("Personajes/Notas", self.toggle_right_panel)])
        self._toolbar_group(groups, 4, "Exportación", [("Exportar historia", self.export_story)])

    def _toolbar_group(self, parent, column: int, title: str, buttons):
        frame = ttk.Frame(parent, style="Toolbar.TFrame", padding=(0, 0, 16, 0))
        frame.grid(row=0, column=column, sticky="w")
        ttk.Label(frame, text=title.upper(), style="GroupTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        row = ttk.Frame(frame, style="Toolbar.TFrame")
        row.grid(row=1, column=0, sticky="w")
        for index, (label, command) in enumerate(buttons):
            ttk.Button(row, text=label, command=command, style="Primary.TButton").grid(row=0, column=index, padx=(0, 5))

    def show_home(self):
        self.editor_view.grid_remove()
        self.home_view.grid()
        self.load_project_records()
        self.update_responsive_layout()

    def show_editor(self):
        self.home_view.grid_remove()
        self.editor_view.grid()
        self.refresh_full_ui()
        self.update_responsive_layout()

    def load_project_records(self):
        self.project_records = self.project_library.load_records()
        previous = self.selected_project_path
        self.project_list.delete(0, tk.END)
        selected_index = None
        for index, record in enumerate(self.project_records):
            info = describe_project(record.path)
            prefix = "★ " if record.pinned else ""
            last_opened = record.last_opened or "Sin apertura reciente"
            self.project_list.insert(tk.END, f"{prefix}{info['title']}   ·   {last_opened}")
            if record.path == previous:
                selected_index = index

        if not self.project_records:
            self.selected_project_path = None
            self.preview_title.config(text="Todavía no tienes proyectos registrados")
            self.preview_subtitle.config(text="")
            self.preview_summary.config(text="Crea uno nuevo o importa un JSON para empezar.")
            self.library_hint.set("Los proyectos que guardes o abras aparecerán aquí.")
            return

        if selected_index is None:
            selected_index = 0
        self.project_list.selection_set(selected_index)
        self.project_list.see(selected_index)
        self.on_project_record_select()

    def on_project_record_select(self, _event=None):
        selection = self.project_list.curselection()
        if not selection:
            self.selected_project_path = None
            return
        record = self.project_records[selection[0]]
        self.selected_project_path = record.path
        info = describe_project(record.path)
        last_opened = record.last_opened or "Aún no abierto desde esta biblioteca"
        self.preview_title.config(text=info["title"])
        self.preview_subtitle.config(text=info["subtitle"])
        self.preview_summary.config(text=f"{info['summary']} · Última apertura: {last_opened}")
        self.library_hint.set("Doble clic para abrir. Usa 'Fijar / quitar' para mantener tus favoritos arriba.")

    def toggle_selected_pin(self):
        if not self.selected_project_path:
            messagebox.showwarning("Selecciona un proyecto", "Elige un proyecto de la lista para fijarlo.")
            return
        self.project_library.toggle_pin(self.selected_project_path)
        self.load_project_records()

    def import_project_json(self):
        filepath = filedialog.askopenfilename(
            title="Importar proyecto JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        try:
            self.controller.repository.load(filepath)
        except ProjectValidationError as error:
            messagebox.showerror("Proyecto inválido", str(error))
            return
        self.project_library.register_path(filepath)
        self.selected_project_path = os.path.abspath(filepath)
        self.load_project_records()

    def open_selected_project(self):
        if not self.selected_project_path:
            messagebox.showwarning("Selecciona un proyecto", "Elige un proyecto de la lista primero.")
            return
        self._open_project_path(self.selected_project_path)

    def _open_project_path(self, path: str):
        try:
            self.controller.open_project(path)
        except ProjectValidationError as error:
            messagebox.showerror("Proyecto inválido", str(error))
            return
        self.project_library.mark_opened(path)
        self.selected_project_path = os.path.abspath(path)
        self.show_editor()

    def update_responsive_layout(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        width = self.root.winfo_width()
        self.layout_mode = "compact" if width < HOME_COMPACT_WIDTH else "wide"
        self._apply_home_layout(width)
        self._apply_editor_layout(width)
        self.update_status_bar()

    def _apply_home_layout(self, width: int):
        if width < HOME_COMPACT_WIDTH:
            self.home_view.columnconfigure(0, weight=1)
            self.home_view.columnconfigure(1, weight=0)
            self.library_card.grid_configure(row=1, column=0, padx=0, pady=(0, 12))
            self.actions_card.grid_configure(row=2, column=0, sticky="ew")
        else:
            self.home_view.columnconfigure(0, weight=3)
            self.home_view.columnconfigure(1, weight=2)
            self.library_card.grid_configure(row=1, column=0, padx=(0, 12), pady=0)
            self.actions_card.grid_configure(row=1, column=1, sticky="nsew")

    def _apply_editor_layout(self, width: int):
        left_hidden = width < EDITOR_TIGHT_WIDTH
        right_hidden = width < EDITOR_COMPACT_WIDTH
        if left_hidden != self.left_panel_auto_hidden:
            self.left_panel_auto_hidden = left_hidden
            self._sync_left_panel_visibility()
        if right_hidden != self.right_panel_auto_hidden:
            self.right_panel_auto_hidden = right_hidden
            self._sync_right_panel_visibility()

    def _pane_has_widget(self, widget) -> bool:
        try:
            return str(widget) in self.main_pane.panes()
        except tk.TclError:
            return False

    def _sync_left_panel_visibility(self):
        should_show = self.left_panel_user_visible and not self.left_panel_auto_hidden
        if should_show and not self._pane_has_widget(self.chapter_tree):
            self.main_pane.add(self.chapter_tree, before=self.chapter_editor, minsize=180, stretch="never")
        elif not should_show and self._pane_has_widget(self.chapter_tree):
            self.main_pane.forget(self.chapter_tree)

    def _sync_right_panel_visibility(self):
        should_show = self.right_panel_user_visible and not self.right_panel_auto_hidden
        if should_show and not self._pane_has_widget(self.right_tabs):
            self.main_pane.add(self.right_tabs, minsize=220, stretch="never")
        elif not should_show and self._pane_has_widget(self.right_tabs):
            self.main_pane.forget(self.right_tabs)

    def toggle_left_panel(self):
        self.left_panel_user_visible = not self.left_panel_user_visible
        self._sync_left_panel_visibility()

    def toggle_right_panel(self):
        self.right_panel_user_visible = not self.right_panel_user_visible
        self._sync_right_panel_visibility()

    def refresh_tree(self, select_id=None):
        self.chapter_tree.clear()
        project = self.controller.project
        if not project:
            return

        def insert_recursive(parent_item, node_id):
            node = project.nodes[node_id]
            item = self.chapter_tree.insert_node(parent_item, node)
            for child_id in node.children:
                insert_recursive(item, child_id)

        for node_id in project.root_ids:
            insert_recursive("", node_id)

        if select_id and select_id in project.nodes:
            self.chapter_tree.select(select_id)

    def refresh_characters(self):
        self.characters_panel.set_character_names(self.controller.get_sorted_character_names())
        self.characters_panel.select_name(self.controller.current_character_name)

    def refresh_full_ui(self):
        self.chapter_editor.set_project(self.controller.project)
        self.refresh_tree(self.controller.current_node_id)
        self.refresh_characters()
        self._sync_selected_node_ui()
        self._sync_selected_character_ui()
        self.update_action_states()
        self._sync_left_panel_visibility()
        self._sync_right_panel_visibility()
        self.update_status_bar()

    def _sync_selected_node_ui(self):
        node = self.controller.get_current_node()
        if node:
            self.chapter_editor.set_enabled(True)
            self.chapter_editor.load_node(node)
            self.notes_panel.set_enabled(True)
            self.notes_panel.load_notes(node.notes)
        else:
            self.chapter_editor.clear()
            self.notes_panel.clear()
            self.notes_panel.set_enabled(False)

    def _sync_selected_character_ui(self):
        character = self.controller.get_current_character()
        has_project = self.controller.project is not None
        self.characters_panel.set_enabled(has_project)
        if character:
            self.characters_panel.select_name(character.name)
            self.characters_panel.load_description(character.description)
            self.characters_panel.set_highlight_enabled(character.highlight_enabled)
            self.characters_panel.set_highlight_color(character.highlight_color)
        else:
            self.characters_panel.select_name(None)
            self.characters_panel.clear_description()
            self.characters_panel.set_highlight_enabled(True)
            self.characters_panel.set_highlight_color("#ffd54f")

    def update_action_states(self):
        node = self.controller.get_current_node()
        self.chapter_editor.set_enabled(node is not None)
        self.notes_panel.set_enabled(node is not None)

    def update_status_bar(self):
        path = self.controller.project_path or "Sin proyecto abierto"
        if len(path) > 48:
            path = "…" + path[-47:]
        path = path.replace("â€¦", "…")
        self.status_project.set(path)
        self.status_dirty.set("Cambios sin guardar" if self.controller.project_modified else "Todo guardado")
        node_path = self.controller.get_node_path(self.controller.current_node_id)
        self.status_selection.set(" / ".join(node.title for node in node_path) if node_path else "Sin selección")

    def load_selected_node(self, node_id):
        self.controller.select_node(node_id)
        self._sync_selected_node_ui()
        self.update_action_states()
        self.update_status_bar()

    def store_current_texts(self):
        project = self.controller.project
        node = self.controller.get_current_node()
        if project and node:
            new_content = self.chapter_editor.get_content()
            new_notes = self.notes_panel.get_notes()
            if node.content != new_content:
                chapter_service.update_node_content(project, node.id, new_content)
                self.controller.mark_modified()
            if node.notes != new_notes:
                chapter_service.update_node_notes(project, node.id, new_notes)
                self.controller.mark_modified()

        character = self.controller.get_current_character()
        if project and character:
            new_desc = self.characters_panel.get_description()
            if character.description != new_desc:
                character_service.update_character_description(project, character.name, new_desc)
                self.controller.mark_modified()
        self.update_status_bar()

    def on_tree_select(self, _event=None):
        selection = self.chapter_tree.selection()
        if not selection:
            return
        self.store_current_texts()
        self.load_selected_node(selection[0])

    def on_tree_context_menu(self, event):
        item = self.chapter_tree.identify_node(event)
        if item:
            self.chapter_tree.select(item)
            self.load_selected_node(item)
        self.tree_menu.tk_popup(event.x_root, event.y_root)

    def on_content_change(self):
        project = self.controller.project
        node = self.controller.get_current_node()
        if project and node:
            new_content = self.chapter_editor.get_content()
            if node.content != new_content:
                chapter_service.update_node_content(project, node.id, new_content)
                self.controller.mark_modified()
                self.update_status_bar()

    def on_notes_change(self):
        project = self.controller.project
        node = self.controller.get_current_node()
        if project and node:
            new_notes = self.notes_panel.get_notes()
            if node.notes != new_notes:
                chapter_service.update_node_notes(project, node.id, new_notes)
                self.controller.mark_modified()
                self.update_status_bar()

    def on_editor_stats_change(self, words: int, characters: int):
        self.status_stats.set(f"{words} palabras · {characters} caracteres")

    def add_story(self):
        if not self.controller.project:
            messagebox.showwarning("Proyecto requerido", MSG_OPEN_PROJECT_FIRST)
            return
        title = simpledialog.askstring("Nueva historia", "Nombre de la historia:")
        if not title:
            return
        node = chapter_service.create_story(self.controller.project, title)
        self.controller.mark_modified()
        self.refresh_tree(select_id=node.id)
        self.load_selected_node(node.id)

    def add_chapter(self):
        if not self.controller.project:
            messagebox.showwarning("Proyecto requerido", MSG_OPEN_PROJECT_FIRST)
            return
        if not self.controller.can_add_chapter():
            messagebox.showwarning("Aviso", MSG_SELECT_STORY)
            return
        title = simpledialog.askstring("Nuevo capítulo", "Nombre del capítulo:")
        if not title:
            return
        try:
            node = chapter_service.create_chapter(self.controller.project, self.controller.current_node_id, title)
        except ChapterStructureError as error:
            messagebox.showwarning("Aviso", str(error))
            return
        self.controller.mark_modified()
        self.refresh_tree(select_id=node.id)
        self.load_selected_node(node.id)

    def add_section(self):
        if not self.controller.project:
            messagebox.showwarning("Proyecto requerido", MSG_OPEN_PROJECT_FIRST)
            return
        if not self.controller.can_add_section():
            messagebox.showwarning("Aviso", MSG_SELECT_CHAPTER)
            return
        title = simpledialog.askstring("Nueva escena", "Nombre de la escena:")
        if not title:
            return
        try:
            node = chapter_service.create_section(self.controller.project, self.controller.current_node_id, title)
        except ChapterStructureError as error:
            messagebox.showwarning("Aviso", str(error))
            return
        self.controller.mark_modified()
        self.refresh_tree(select_id=node.id)
        self.load_selected_node(node.id)

    def export_story(self):
        if not self.controller.project:
            messagebox.showwarning("Proyecto requerido", MSG_OPEN_PROJECT_FIRST)
            return
        if not self.controller.current_node_id:
            messagebox.showwarning("Aviso", "Selecciona una historia o un nodo dentro de ella para exportar.")
            return
        export_dir = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not export_dir:
            return
        try:
            export_story_service(self.controller.project, self.controller.current_node_id, export_dir)
            messagebox.showinfo("Exportación", "Historia exportada correctamente.")
        except Exception as error:
            messagebox.showerror("Error", f"Error al exportar: {error}")

    def rename_node(self):
        node = self.controller.get_current_node()
        if not node:
            messagebox.showwarning("Aviso", MSG_SELECT_NODE)
            return
        new_title = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=node.title)
        if not new_title:
            return
        chapter_service.rename_node(self.controller.project, node.id, new_title)
        self.controller.mark_modified()
        self.refresh_tree(select_id=node.id)
        self.load_selected_node(node.id)

    def delete_node(self):
        node = self.controller.get_current_node()
        if not node:
            messagebox.showwarning("Aviso", MSG_SELECT_NODE)
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar '{node.title}' y todo su contenido?"):
            return
        chapter_service.delete_node_recursive(self.controller.project, node.id)
        self.controller.mark_modified()
        self.controller.select_node(None)
        self.refresh_tree()
        self._sync_selected_node_ui()
        self.update_action_states()
        self.update_status_bar()

    def add_character(self):
        if not self.controller.project:
            messagebox.showwarning("Proyecto requerido", MSG_OPEN_PROJECT_FIRST)
            return
        name = simpledialog.askstring("Nuevo personaje", "Nombre del personaje:")
        if not name:
            return
        try:
            character_service.create_character(self.controller.project, name)
            self.controller.mark_modified()
            self.refresh_characters()
            self.chapter_editor.refresh_character_highlights(force=True)
        except ValueError as error:
            messagebox.showerror("Error", str(error))

    def rename_character(self):
        name = self.characters_panel.get_selected_name()
        if not name:
            messagebox.showwarning("Aviso", MSG_SELECT_CHARACTER)
            return
        new_name = simpledialog.askstring("Renombrar personaje", "Nuevo nombre:", initialvalue=name)
        if not new_name:
            return
        try:
            character_service.rename_character(self.controller.project, name, new_name)
            self.controller.mark_modified()
            self.controller.select_character(new_name)
            self.refresh_characters()
            self._sync_selected_character_ui()
            self.chapter_editor.refresh_character_highlights(force=True)
            self.update_status_bar()
        except ValueError as error:
            messagebox.showerror("Error", str(error))

    def delete_character(self):
        name = self.characters_panel.get_selected_name()
        if not name:
            messagebox.showwarning("Aviso", MSG_SELECT_CHARACTER)
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar personaje '{name}'?"):
            return
        character_service.delete_character(self.controller.project, name)
        self.controller.mark_modified()
        self.controller.select_character(None)
        self.refresh_characters()
        self._sync_selected_character_ui()
        self.chapter_editor.refresh_character_highlights(force=True)
        self.update_status_bar()

    def on_character_select(self, _event=None):
        self.store_current_texts()
        self.controller.select_character(self.characters_panel.get_selected_name())
        self._sync_selected_character_ui()
        self.update_status_bar()

    def on_character_highlight_change(self):
        name = self.characters_panel.get_selected_name()
        if not name or not self.controller.project:
            return
        character_service.set_character_highlight_enabled(self.controller.project, name, self.characters_panel.get_highlight_enabled())
        self.controller.mark_modified()
        self.chapter_editor.refresh_character_highlights(force=True)
        self.update_status_bar()

    def on_character_color_change(self):
        name = self.characters_panel.get_selected_name()
        if not name or not self.controller.project:
            return
        character_service.set_character_highlight_color(self.controller.project, name, self.characters_panel.get_highlight_color())
        self.controller.mark_modified()
        self.chapter_editor.refresh_character_highlights(force=True)
        self.update_status_bar()

    def check_unsaved_changes(self) -> bool:
        self.store_current_texts()
        if self.controller.project and self.controller.project_modified:
            answer = messagebox.askyesnocancel("Cambios sin guardar", "¿Deseas guardar el proyecto actual antes de continuar?")
            if answer is None:
                return False
            if answer is True:
                self.save()
        return True

    def new_project(self):
        if self.controller.project and not self.check_unsaved_changes():
            return
        filepath = filedialog.asksaveasfilename(title="Nuevo proyecto", defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not filepath:
            return
        self.controller.new_project(filepath)
        self.project_library.register_path(filepath)
        self.project_library.mark_opened(filepath)
        self.selected_project_path = os.path.abspath(filepath)
        self.show_editor()

    def open_project(self):
        if self.controller.project and not self.check_unsaved_changes():
            return
        filepath = filedialog.askopenfilename(title="Abrir proyecto", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not filepath:
            return
        self.project_library.register_path(filepath)
        self._open_project_path(filepath)

    def close_project(self):
        if self.controller.project and not self.check_unsaved_changes():
            return
        self.controller.close_project()
        self.status_stats.set("0 palabras · 0 caracteres")
        self.show_home()

    def save(self):
        if not self.controller.project:
            return
        self.store_current_texts()
        if not self.controller.project_path:
            self.save_as()
            return
        self.controller.save()
        self.project_library.register_path(self.controller.project_path)
        self.project_library.mark_opened(self.controller.project_path)
        self.update_status_bar()
        messagebox.showinfo("Guardado", MSG_SAVED)

    def save_as(self):
        if not self.controller.project:
            return
        self.store_current_texts()
        filepath = filedialog.asksaveasfilename(title="Guardar como...", defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not filepath:
            return
        self.controller.save_as(filepath)
        self.project_library.register_path(filepath)
        self.project_library.mark_opened(filepath)
        self.selected_project_path = os.path.abspath(filepath)
        self.update_status_bar()
        messagebox.showinfo("Guardado", MSG_SAVED)

    def on_close(self):
        if self.controller.project and not self.check_unsaved_changes():
            return
        self.root.destroy()
