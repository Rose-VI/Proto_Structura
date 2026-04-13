import tkinter as tk

from app.paths import get_resource_path
from app.ui.main_window import MainWindow


def configure_app_icon(root: tk.Tk) -> None:
    icon_path = get_resource_path("icon/Structura.ico")
    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except tk.TclError:
            pass

def main():
    root = tk.Tk()
    configure_app_icon(root)
    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
