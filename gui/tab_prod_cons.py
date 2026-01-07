import tkinter as tk
from tkinter import ttk
from utils.buffer import ThreadSafeBuffer
from threads.producer import ProducerThread
from threads.consumer import ConsumerThread
from utils.debug_controller import DebugController
import time


class ProdConsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)

        self.buffer_max = 100
        self.buffer = ThreadSafeBuffer(max_size=self.buffer_max)

        self._debug = DebugController()
        self.buffer.set_debug(self._debug)

        self._log_win = None
        self._log_text = None
        self._log_job = None
        self._log_pos = 0

        self._produced = tk.IntVar(value=0)
        self._consumed = tk.IntVar(value=0)

        self._build_ui()
        self._wire_threads()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        debug_frame = ttk.LabelFrame(container, text="Debug (Dekker)")
        debug_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        dbg_row = ttk.Frame(debug_frame)
        dbg_row.pack(fill=tk.X, padx=10, pady=8)
        self._debug_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(dbg_row, text="Включить", variable=self._debug_enabled).pack(side=tk.LEFT)
        ttk.Button(dbg_row, text="Шаг", command=self._debug.step).pack(side=tk.LEFT, padx=6)
        ttk.Button(dbg_row, text="Авто", command=self._debug.run).pack(side=tk.LEFT, padx=6)
        ttk.Button(dbg_row, text="Пауза", command=self._debug.pause).pack(side=tk.LEFT)
        ttk.Button(dbg_row, text="Лог", command=self._open_log).pack(side=tk.LEFT, padx=6)

        state_row = ttk.Frame(debug_frame)
        state_row.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._dbg_point_lbl = ttk.Label(state_row, text="point: -")
        self._dbg_point_lbl.pack(side=tk.LEFT)
        self._dekker_lbl = ttk.Label(state_row, text="flag0: False | flag1: False | turn: 0")
        self._dekker_lbl.pack(side=tk.LEFT, padx=(10, 0))

        def on_dbg_toggle(*_):
            enabled = bool(self._debug_enabled.get())
            self._debug.set_enabled(enabled)
            if enabled:
                self._debug.pause()

        self._debug_enabled.trace_add("write", on_dbg_toggle)

        # Buffer view and progress
        left = ttk.LabelFrame(container, text="Буфер")
        left.grid(row=1, column=0, sticky="nsew")
        right = ttk.LabelFrame(container, text="Управление")
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

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
        stats.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
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
        container.rowconfigure(1, weight=1)

        self.after(300, self._poll_buffer_view)

    def _open_log(self):
        if self._log_win is not None and self._log_win.winfo_exists():
            try:
                self._log_win.lift()
                self._log_win.focus_force()
            except Exception:
                pass
            return

        self._log_win = tk.Toplevel(self)
        self._log_win.title("Лог (Dekker)")
        self._log_win.geometry("780x420")

        top = ttk.Frame(self._log_win)
        top.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(top, text="Очистить лог", command=self._clear_log).pack(side=tk.LEFT)

        body = ttk.Frame(self._log_win)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        yscroll = ttk.Scrollbar(body, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text = tk.Text(body, wrap=tk.NONE, yscrollcommand=yscroll.set)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.configure(command=self._log_text.yview)

        self._log_pos = 0

        def on_close():
            try:
                if self._log_job is not None:
                    self.after_cancel(self._log_job)
            except Exception:
                pass
            self._log_job = None
            self._log_win.destroy()

        self._log_win.protocol("WM_DELETE_WINDOW", on_close)
        self._poll_log()

    def _clear_log(self):
        try:
            self._debug.clear_log()
        except Exception:
            pass
        self._log_pos = 0
        if self._log_text is not None:
            self._log_text.delete("1.0", tk.END)

    def _poll_log(self):
        if self._log_win is None or not self._log_win.winfo_exists():
            return

        try:
            lines = self._debug.log_snapshot()
            if self._log_text is not None and self._log_pos < len(lines):
                chunk = "\n".join(lines[self._log_pos:])
                if chunk:
                    if self._log_pos != 0:
                        chunk = "\n" + chunk
                    self._log_text.insert(tk.END, chunk)
                    self._log_text.see(tk.END)
                self._log_pos = len(lines)
        except Exception:
            pass

        self._log_job = self.after(250, self._poll_log)

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

        try:
            point, _state = self._debug.snapshot()
            self._dbg_point_lbl.configure(text=f"point: {point or '-'}")
            d = self.buffer.dekker_snapshot()
            self._dekker_lbl.configure(text=f"flag0: {d['flag0']} | flag1: {d['flag1']} | turn: {d['turn']}")
        except Exception:
            pass
        self.after(400, self._poll_buffer_view)

    def _on_produced(self, item):
        self._produced.set(self._produced.get() + 1)

    def _on_consumed(self, item):
        self._consumed.set(self._consumed.get() + 1)

    def shutdown(self):
        self.producer.stop()
        self.consumer.stop()
