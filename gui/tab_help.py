import tkinter as tk
from tkinter import ttk


class HelpTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = ttk.Label(container, text="Справка", font=("Segoe UI", 16, "bold"))
        title.pack(anchor=tk.W, pady=(0, 10))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=yscroll.set,
            padx=10,
            pady=10,
            borderwidth=1,
            relief=tk.SOLID,
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.configure(command=self.text.yview)

        self._configure_tags()
        self._fill_content()
        self.text.configure(state=tk.DISABLED)

    def _configure_tags(self):
        self.text.tag_configure("h1", font=("Segoe UI", 14, "bold"), spacing1=8, spacing3=6)
        self.text.tag_configure("h2", font=("Segoe UI", 12, "bold"), spacing1=6, spacing3=4)
        self.text.tag_configure("body", font=("Segoe UI", 11), spacing1=2, spacing3=2)
        self.text.tag_configure("bullet", font=("Segoe UI", 11), lmargin1=18, lmargin2=36, spacing1=1, spacing3=1)
        self.text.tag_configure("mono", font=("Consolas", 10))

    def _add_h1(self, s: str):
        self.text.insert(tk.END, s + "\n", ("h1",))

    def _add_h2(self, s: str):
        self.text.insert(tk.END, s + "\n", ("h2",))

    def _add_body(self, s: str):
        self.text.insert(tk.END, s + "\n", ("body",))

    def _add_bullet(self, s: str):
        self.text.insert(tk.END, "- " + s + "\n", ("bullet",))

    def _fill_content(self):
        self._add_h1("О программе")
        self._add_body(
            "Это учебное приложение демонстрирует взаимодействие параллельных потоков и способы синхронизации доступа к общим ресурсам. "
            "Интерфейс разделён на вкладки с отдельными задачами."
        )

        self._add_h1("Задача 1: Запись в файл")
        self._add_body(
            "Цель: показать, как два потока могут писать в один и тот же файл и почему нужен мьютекс для защиты критической секции."
        )
        self._add_h2("Что происходит")
        self._add_bullet("Поток пользователя берёт введённый текст и добавляет его в файл.")
        self._add_bullet("Поток времени периодически дописывает текущие часы/минуты/секунды.")
        self._add_bullet("Запись выполняется внутри мьютекса, чтобы операции не пересекались.")
        self._add_h2("Управление")
        self._add_bullet("Можно менять задержку каждого потока отдельно.")
        self._add_bullet("Файл можно выбрать вручную и очищать кнопкой 'Очистить'.")

        self._add_h1("Задача 2: Производитель–потребитель")
        self._add_body(
            "Цель: продемонстрировать классическую задачу синхронизации, где один поток производит элементы, а другой их потребляет через общий буфер ограниченного размера."
        )
        self._add_h2("Буфер")
        self._add_bullet("Производитель помещает элементы в общий потокобезопасный буфер.")
        self._add_bullet("Потребитель извлекает элементы из этого буфера.")
        self._add_bullet("Интерфейс показывает текущее содержимое и заполненность буфера.")

        self._add_h1("Синхронизация")
        self._add_body(
            "Мьютекс (mutex) обеспечивает взаимное исключение: в любой момент времени только один поток может находиться в критической секции. "
            "Это защищает общий ресурс (например, файл) от гонок, повреждения данных и непредсказуемого результата."
        )

        self.text.insert(tk.END, "\n")
        self._add_body("Подсказка: если поток был остановлен, его можно запускать повторно через кнопку 'Запуск'.")
