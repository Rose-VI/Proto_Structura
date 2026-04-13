import tkinter as tk


class AutocompletePopup:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.transient(parent)

        self.listbox = tk.Listbox(self.window, height=6)
        self.listbox.pack(fill="both", expand=True)

    def show(self, items, x, y):
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)

        if items:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        height = min(140, 24 * max(1, len(items)))
        self.window.geometry(f"260x{height}+{x}+{y}")
        self.window.deiconify()
        self.window.lift()

    def hide(self):
        self.window.withdraw()

    def is_visible(self):
        return self.window.state() != "withdrawn"

    def get_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])

    def select_next(self):
        size = self.listbox.size()
        if size == 0:
            return
        cur = self.listbox.curselection()
        idx = cur[0] if cur else 0
        idx = min(idx + 1, size - 1)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)

    def select_previous(self):
        size = self.listbox.size()
        if size == 0:
            return
        cur = self.listbox.curselection()
        idx = cur[0] if cur else 0
        idx = max(idx - 1, 0)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
