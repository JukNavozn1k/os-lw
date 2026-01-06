import tkinter as tk
from tkinter import ttk, messagebox
from gui.tab_file_write import FileWriteTab
from gui.tab_prod_cons import ProdConsTab
from gui.tab_help import HelpTab


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self._make_style()
        self._build()
        self._bind_close()

    def _make_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Status.OK.TLabel", foreground="#0a7d00")
        style.configure("Status.PAUSED.TLabel", foreground="#b36b00")
        style.configure("Status.STOP.TLabel", foreground="#b30000")

    def _build(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab1 = FileWriteTab(notebook)
        self.tab2 = ProdConsTab(notebook)
        self.tab3 = HelpTab(notebook)

        notebook.add(self.tab1, text="Запись в файл")
        notebook.add(self.tab2, text="Производитель-потребитель")
        notebook.add(self.tab3, text="Справка")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _bind_close(self):
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        try:
            self.tab1.shutdown()
        except Exception:
            pass
        try:
            self.tab2.shutdown()
        except Exception:
            pass
        self.master.destroy()
