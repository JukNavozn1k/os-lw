import tkinter as tk
from tkinter import ttk
import queue
from threads.file_writer import FileWriterThread, TimeWriterThread
from synchronization.mutex_manager import SharedMutex
from utils.file_manager import read_all_text
import os


class FileWriteTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.mutex = SharedMutex()
        self.text_queue: "queue.Queue[str]" = queue.Queue()
        self.file_path = os.path.abspath("user.txt")

        self.user_thread = FileWriterThread(self.text_queue, self.file_path, self.mutex)
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

        # Controls
        controls = ttk.Frame(container)
        controls.pack(fill=tk.X)

        self._thread_controls(controls, 0, "Поток пользователя", self.user_thread)
        self._thread_controls(controls, 1, "Поток времени", self.time_thread)

        # File view
        file_frame = ttk.LabelFrame(container, text=f"Содержимое файла: {self.file_path}")
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.file_text = tk.Text(file_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.file_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        refresh = ttk.Button(container, text="Обновить просмотр файла", command=self._refresh_file_view)
        refresh.pack(anchor=tk.E, pady=(6, 0))

    def _thread_controls(self, parent, col, title, thread_obj):
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))

        # Speed
        spd = ttk.Scale(frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL,
                        command=lambda v, t=thread_obj: t.set_delay(float(v)))
        spd.set(0.5)
        thread_obj.set_delay(0.5)
        ttk.Label(frame, text="Задержка (с)").pack(anchor=tk.W, padx=10, pady=(8, 0))
        spd.pack(fill=tk.X, padx=10)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(btns, text="Запуск", command=thread_obj.start_safe).pack(side=tk.LEFT)
        ttk.Button(btns, text="Пауза", command=thread_obj.pause).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Возобновить", command=thread_obj.resume).pack(side=tk.LEFT)
        ttk.Button(btns, text="Останов", command=thread_obj.stop).pack(side=tk.LEFT, padx=5)

        status = ttk.Label(frame, text="STOP", style="Status.STOP.TLabel")
        status.pack(anchor=tk.W, padx=10, pady=(0, 10))

        def poll_status():
            st = thread_obj.status
            if st == "RUNNING":
                status.configure(text=st, style="Status.OK.TLabel")
            elif st == "PAUSED":
                status.configure(text=st, style="Status.PAUSED.TLabel")
            else:
                status.configure(text=st, style="Status.STOP.TLabel")
            self.after(300, poll_status)

        poll_status()

    def _add_text(self):
        text = self.entry.get()
        if not text:
            return
        for ch in text:
            self.text_queue.put(ch)
        self.text_queue.put("\n")
        self.entry.delete(0, tk.END)

    def _refresh_file_view(self):
        content = read_all_text(self.file_path)
        self.file_text.configure(state=tk.NORMAL)
        self.file_text.delete("1.0", tk.END)
        self.file_text.insert("1.0", content)
        self.file_text.configure(state=tk.DISABLED)
        self.after(1000, self._refresh_file_view)

    def shutdown(self):
        self.user_thread.stop()
        self.time_thread.stop()
