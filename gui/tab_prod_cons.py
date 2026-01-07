import tkinter as tk
from tkinter import ttk
from utils.buffer import ThreadSafeBuffer
from threads.producer import ProducerThread
from threads.consumer import ConsumerThread
import time


class ProdConsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)

        self.buffer_max = 100
        self.buffer = ThreadSafeBuffer(max_size=self.buffer_max)

        self._produced = tk.IntVar(value=0)
        self._consumed = tk.IntVar(value=0)

        self._build_ui()
        self._wire_threads()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buffer view and progress
        left = ttk.LabelFrame(container, text="Буфер")
        left.grid(row=0, column=0, sticky="nsew")
        right = ttk.LabelFrame(container, text="Управление")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.listbox = tk.Listbox(left, height=18)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.progress = ttk.Progressbar(left, mode="determinate", maximum=self.buffer_max)
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Controls for producer and consumer
        self._prod_controls = self._thread_controls(right, title="Производитель")
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        self._cons_controls = self._thread_controls(right, title="Потребитель")

        # Stats
        stats = ttk.LabelFrame(container, text="Статистика")
        stats.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(stats, textvariable=self._produced).pack(side=tk.LEFT, padx=10, pady=6)
        ttk.Label(stats, text="— произведено").pack(side=tk.LEFT)
        ttk.Label(stats, text="  |  ").pack(side=tk.LEFT)
        ttk.Label(stats, textvariable=self._consumed).pack(side=tk.LEFT)
        ttk.Label(stats, text="— потреблено").pack(side=tk.LEFT)
        ttk.Label(stats, text="  |  ").pack(side=tk.LEFT)
        self._buf_size_lbl = ttk.Label(stats, text="Буфер: 0")
        self._buf_size_lbl.pack(side=tk.LEFT)

        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        self.after(300, self._poll_buffer_view)

    def _thread_controls(self, parent, title: str):
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X)

        spd = ttk.Scale(frame, from_=0.5, to=5.0, orient=tk.HORIZONTAL)
        spd.set(1.0)
        ttk.Label(frame, text="Задержка (с)").pack(anchor=tk.W, padx=10, pady=(8, 0))
        spd.pack(fill=tk.X, padx=10)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, padx=10, pady=8)
        start_b = ttk.Button(btns, text="Запуск")
        stop_b = ttk.Button(btns, text="Останов")
        start_b.pack(side=tk.LEFT)
        stop_b.pack(side=tk.LEFT, padx=5)

        status_row = ttk.Frame(frame)
        status_row.pack(anchor=tk.W, padx=10, pady=(0, 10), fill=tk.X)
        status_row.columnconfigure(0, weight=0)
        status_row.columnconfigure(1, weight=0)
        status = ttk.Label(status_row, text="STOP", style="Status.STOP.TLabel")
        status.grid(row=0, column=0, sticky="w")
        pulse = ttk.Label(status_row, text="●", style="Pulse.STOP.TLabel")
        pulse.grid(row=0, column=1, sticky="w", padx=(8, 0))

        return {
            "frame": frame,
            "speed": spd,
            "start": start_b,
            "stop": stop_b,
            "status": status,
            "pulse": pulse,
        }

    def _wire_threads(self):
        self.producer = ProducerThread(self.buffer, on_produced=self._on_produced)
        self.consumer = ConsumerThread(self.buffer, on_consumed=self._on_consumed)

        prod_active_until = 0.0
        cons_active_until = 0.0

        def mark_active(is_prod: bool):
            nonlocal prod_active_until, cons_active_until
            if is_prod:
                prod_active_until = time.time() + 0.45
            else:
                cons_active_until = time.time() + 0.45

        # Wire speeds
        self._prod_controls["speed"].configure(command=lambda v: self.producer.set_delay(float(v)))
        self._cons_controls["speed"].configure(command=lambda v: self.consumer.set_delay(float(v)))
        self.producer.set_delay(self._prod_controls["speed"].get())
        self.consumer.set_delay(self._cons_controls["speed"].get())

        # Wire buttons
        self._prod_controls["start"].configure(command=self.producer.start_safe)
        self._prod_controls["stop"].configure(command=self.producer.stop)

        self._cons_controls["start"].configure(command=self.consumer.start_safe)
        self._cons_controls["stop"].configure(command=self.consumer.stop)

        # Status polling
        def poll_status():
            for ctrl, th in ((self._prod_controls, self.producer), (self._cons_controls, self.consumer)):
                st = th.status
                if st == "STOP":
                    ctrl["status"].configure(text=st, style="Status.STOP.TLabel")
                    ctrl["pulse"].configure(style="Pulse.STOP.TLabel")
                else:
                    if th.consume_pulse():
                        mark_active(th is self.producer)

                    now = time.time()
                    active_until = prod_active_until if th is self.producer else cons_active_until
                    if now < active_until:
                        ctrl["status"].configure(text=st, style="Status.OK.TLabel")
                        ctrl["pulse"].configure(style="Pulse.ACTIVE.TLabel")
                    else:
                        ctrl["status"].configure(text="WAITING", style="Status.WAIT.TLabel")
                        ctrl["pulse"].configure(style="Pulse.WAIT.TLabel")
            self.after(300, poll_status)

        poll_status()

    def _poll_buffer_view(self):
        # Update listbox snapshot
        items = list(self.buffer.snapshot())[-50:]  # show tail
        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, str(it))
        size = self.buffer.size()
        self.progress.configure(value=size)
        self._buf_size_lbl.configure(text=f"Буфер: {size}")
        self.after(400, self._poll_buffer_view)

    def _on_produced(self, item):
        self._produced.set(self._produced.get() + 1)

    def _on_consumed(self, item):
        self._consumed.set(self._consumed.get() + 1)

    def shutdown(self):
        self.producer.stop()
        self.consumer.stop()
