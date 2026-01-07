import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import queue
import time
from threads.file_writer import FileWriterThread, TimeWriterThread
from synchronization.mutex_manager import SharedMutex
from utils.file_manager import read_all_text, clear_file
import os


class FileWriteTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.mutex = SharedMutex()
        self.text_queue: "queue.Queue[str]" = queue.Queue()
        self.file_path = os.path.abspath("user.txt")

        self._entered_text = ""
        self._file_path_var = tk.StringVar(value=self.file_path)

        self._refresh_job = None

        self.user_thread = FileWriterThread(
            self.text_queue,
            self.file_path,
            self.mutex,
            on_before_write=self._on_before_user_write,
        )
        self.time_thread = TimeWriterThread(self.file_path, self.mutex)

        self._build_ui()
        self._refresh_file_view()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        input_frame = ttk.LabelFrame(container, text="Ввод текста")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.entry = ttk.Entry(input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=10)

        add_btn = ttk.Button(input_frame, text="Добавить текст", command=self._add_text)
        add_btn.pack(side=tk.LEFT, padx=(5, 10))

        lorem_btn = ttk.Button(input_frame, text="Lorem ipsum", command=self._fill_lorem)
        lorem_btn.pack(side=tk.LEFT, padx=(0, 10))

        entered_frame = ttk.LabelFrame(container, text="Введённый текст")
        entered_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.entered_text = tk.Text(entered_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.entered_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Controls
        controls = ttk.Frame(container)
        controls.pack(fill=tk.X)

        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)

        self.user_speed = self._thread_controls(controls, 0, "Поток пользователя", lambda: self.user_thread)
        self.time_speed = self._thread_controls(controls, 1, "Поток времени", lambda: self.time_thread)

        file_ctrl = ttk.LabelFrame(controls, text="Файл")
        file_ctrl.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        path_row = ttk.Frame(file_ctrl)
        path_row.pack(fill=tk.X, padx=10, pady=(10, 6))
        ttk.Label(path_row, text="Путь:").pack(side=tk.LEFT)
        ttk.Label(path_row, textvariable=self._file_path_var).pack(side=tk.LEFT, padx=(6, 6), fill=tk.X, expand=True)
        ttk.Button(path_row, text="...", width=3, command=self._choose_file).pack(side=tk.RIGHT)

        btn_row = ttk.Frame(file_ctrl)
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_row, text="Очистить", command=self._clear_current_file).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Обновить", command=self._render_file_content).pack(side=tk.RIGHT)

        self.file_frame = ttk.LabelFrame(container, text=f"Содержимое файла: {self.file_path}")
        self.file_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.file_text = tk.Text(self.file_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.file_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _thread_controls(self, parent, col, title, thread_getter):
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))

        # Speed
        spd = ttk.Scale(frame, from_=0.5, to=5.0, orient=tk.HORIZONTAL,
                        command=lambda v: thread_getter().set_delay(float(v)))
        spd.set(1.0)
        thread_getter().set_delay(1.0)
        ttk.Label(frame, text="Задержка (с)").pack(anchor=tk.W, padx=10, pady=(8, 0))
        spd.pack(fill=tk.X, padx=10)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(btns, text="Запуск", command=lambda: thread_getter().start_safe()).pack(side=tk.LEFT)
        ttk.Button(btns, text="Останов", command=lambda: thread_getter().stop()).pack(side=tk.LEFT, padx=5)

        status_row = ttk.Frame(frame)
        status_row.pack(anchor=tk.W, padx=10, pady=(0, 10), fill=tk.X)
        status_row.columnconfigure(0, weight=0)
        status_row.columnconfigure(1, weight=0)
        status = ttk.Label(status_row, text="STOP", style="Status.STOP.TLabel")
        status.grid(row=0, column=0, sticky="w")
        pulse = ttk.Label(status_row, text="●", style="Pulse.STOP.TLabel")
        pulse.grid(row=0, column=1, sticky="w", padx=(8, 0))

        active_until = 0.0

        def mark_active():
            nonlocal active_until
            active_until = time.time() + 0.45
            pulse.configure(style="Pulse.ACTIVE.TLabel")

        def poll_status():
            st = thread_getter().status
            if st == "STOP":
                status.configure(text=st, style="Status.STOP.TLabel")
                pulse.configure(style="Pulse.STOP.TLabel")
            else:
                if thread_getter().consume_pulse():
                    mark_active()

                if time.time() < active_until:
                    status.configure(text=st, style="Status.OK.TLabel")
                    pulse.configure(style="Pulse.ACTIVE.TLabel")
                else:
                    status.configure(text="WAITING", style="Status.WAIT.TLabel")
                    pulse.configure(style="Pulse.WAIT.TLabel")
            self.after(300, poll_status)

        poll_status()
        return spd

    def _choose_file(self):
        selected = filedialog.asksaveasfilename(
            title="Выбор файла",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.file_path) or ".",
            initialfile=os.path.basename(self.file_path),
        )
        if not selected:
            return
        self._set_file_path(os.path.abspath(selected))

    def _set_file_path(self, new_path: str):
        if os.path.abspath(new_path) == os.path.abspath(self.file_path):
            return

        self.user_thread.stop()
        self.time_thread.stop()

        self.file_path = new_path
        self._file_path_var.set(self.file_path)
        self.user_thread = FileWriterThread(
            self.text_queue,
            self.file_path,
            self.mutex,
            on_before_write=self._on_before_user_write,
        )
        self.time_thread = TimeWriterThread(self.file_path, self.mutex)

        if hasattr(self, "user_speed"):
            self.user_thread.set_delay(float(self.user_speed.get()))
        if hasattr(self, "time_speed"):
            self.time_thread.set_delay(float(self.time_speed.get()))

        if hasattr(self, "file_frame"):
            self.file_frame.configure(text=f"Содержимое файла: {self.file_path}")
        self._render_file_content()

    def _add_text(self):
        text = self.entry.get()
        if not text:
            return

        self._entered_text += text
        self._render_entered_text()
        for ch in text:
            self.text_queue.put(ch)
        self.text_queue.put("\n")
        self._entered_text += "\n"
        self._render_entered_text()
        self.entry.delete(0, tk.END)

    def _fill_lorem(self):
        lorem = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
            "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )
        self.entry.delete(0, tk.END)
        self.entry.insert(0, lorem)
        self.entry.focus_set()

    def _on_before_user_write(self, ch: str, ack):
        def apply():
            if ch and self._entered_text:
                if self._entered_text.startswith(ch):
                    self._entered_text = self._entered_text[1:]
                else:
                    idx = self._entered_text.find(ch)
                    if idx != -1:
                        self._entered_text = self._entered_text[:idx] + self._entered_text[idx + 1 :]
            self._render_entered_text()
            ack.set()

        self.after(0, apply)

    def _render_entered_text(self):
        if not hasattr(self, "entered_text"):
            return
        self.entered_text.configure(state=tk.NORMAL)
        self.entered_text.delete("1.0", tk.END)
        self.entered_text.insert("1.0", self._entered_text)
        self.entered_text.configure(state=tk.DISABLED)

    def _clear_current_file(self):
        with self.mutex:
            clear_file(self.file_path)
        self._render_file_content()

    def _render_file_content(self):
        content = read_all_text(self.file_path)
        self.file_text.configure(state=tk.NORMAL)
        self.file_text.delete("1.0", tk.END)
        self.file_text.insert("1.0", content)
        self.file_text.configure(state=tk.DISABLED)

    def _refresh_file_view(self):
        self._render_file_content()
        self._refresh_job = self.after(1000, self._refresh_file_view)

    def shutdown(self):
        self.user_thread.stop()
        self.time_thread.stop()
