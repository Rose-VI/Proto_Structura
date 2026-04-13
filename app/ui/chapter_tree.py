import tkinter as tk
from tkinter import ttk

from app.models import NodeType


NODE_LABELS = {
    NodeType.STORY: "● Historia",
    NodeType.CHAPTER: "◌ Capítulo",
    NodeType.SECTION: "– Escena",
}


class ChapterTree(ttk.Frame):
    def __init__(self, parent, on_select):
        super().__init__(parent, padding=10)

        self.on_select_callback = on_select
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Estructura", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", on_select)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert_node(self, parent, node):
        label = f"{NODE_LABELS[node.node_type]}  {node.title}"
        tags = (node.node_type.value,)
        return self.tree.insert(parent, "end", iid=node.id, text=label, open=True, tags=tags)

    def selection(self):
        return self.tree.selection()

    def select(self, node_id):
        self.tree.selection_set(node_id)
        self.tree.focus(node_id)
        self.tree.see(node_id)

    def remove_node(self, node_id: str):
        if self.tree.exists(node_id):
            self.tree.delete(node_id)

    def update_node(self, node):
        label = f"{NODE_LABELS[node.node_type]}  {node.title}"
        if self.tree.exists(node.id):
            self.tree.item(node.id, text=label, tags=(node.node_type.value,))

    def move_node(self, node, parent_id: str | None):
        if self.tree.exists(node.id):
            parent = parent_id or ""
            self.tree.move(node.id, parent, "end")

    def bind_context_menu(self, callback):
        self.tree.bind("<Button-3>", callback)

    def identify_node(self, event: tk.Event) -> str | None:
        item = self.tree.identify_row(event.y)
        return item or None
