import tkinter as tk
from gui.main_window import MainWindow


def run_app():
    root = tk.Tk()
    root.title("SyncLab")
    root.geometry("1000x700")
    try:
        icon = tk.PhotoImage(file="assets/logo.png")
        root.iconphoto(True, icon)
    except Exception:
        pass
    # Windows scaling friendliness
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
    except Exception:
        pass
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
