# Небольшое окно для запуска и сравнения результатов лабораторной.

import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from lab_actions import COLOR, FIELDS, HINTS, MODES, make_variants
from smoothing import absolute_difference


class LabApp(tk.Tk):
    # Открыть изображение, запустить операцию и выбрать результат.

    def __init__(self):
        super().__init__()
        self.title("Лабораторная 3 — обработка изображений")
        self.geometry("1120x720")
        self.minsize(900, 600)

        # Храним исходник и готовые варианты в полном размере.
        self.source = None
        self.results = []                 # (подпись, полное изображение)
        self.preview_images = []          # ссылки для Tkinter
        # StringVar связывает выбранный пункт и операцию с выпадающими списками.
        self.mode = tk.StringVar(value=COLOR)
        self.operation = tk.StringVar()
        self.status = tk.StringVar(value="Откройте изображение для начала работы.")

        self._build()
        self._change_mode()

    # Создание окна ---------------------------------------------------------

    def _build(self):
        # Собрать окно из панели команд, полей, списка и предпросмотра.
        self._build_toolbar()
        self._build_parameters()
        # Основная область: слева список, справа три изображения.
        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        self._build_result_list(body)
        self._build_preview(body)
        ttk.Label(self, textvariable=self.status, padding=10).pack(fill="x")

    def _build_toolbar(self):
        # Кнопки и два выпадающих списка.
        bar = ttk.Frame(self, padding=10)
        bar.pack(fill="x")
        ttk.Button(bar, text="Открыть изображение", command=self._open).grid(row=0, column=0, padx=4)
        ttk.Label(bar, text="Пункт:").grid(row=0, column=1, padx=4)
        modes = ttk.Combobox(bar, textvariable=self.mode, values=list(MODES), state="readonly", width=19)
        modes.grid(row=0, column=2, padx=4)
        # После выбора пункта обновляем доступные операции.
        modes.bind("<<ComboboxSelected>>", lambda event: self._change_mode())
        ttk.Label(bar, text="Операция:").grid(row=0, column=3, padx=4)
        self.operations = ttk.Combobox(bar, textvariable=self.operation, state="readonly", width=25)
        self.operations.grid(row=0, column=4, padx=4)
        # После выбора операции обновляем подписи и значения полей.
        self.operations.bind("<<ComboboxSelected>>", lambda event: self._change_operation())
        ttk.Button(bar, text="Применить / сравнить", command=self._apply).grid(row=0, column=5, padx=4)
        ttk.Button(bar, text="Сохранить выбранное", command=self._save).grid(row=0, column=6, padx=4)

    def _build_parameters(self):
        # Три поля; для выбранной операции видны только нужные.
        frame = ttk.Frame(self, padding=(14, 8))
        frame.pack(fill="x")
        self.parameter_labels = []
        self.parameter_entries = []
        # Трёх полей хватает даже для диапазона с константой и сигма-фильтра.
        for index in range(3):
            label = ttk.Label(frame)
            entry = ttk.Entry(frame, width=18)
            label.grid(row=0, column=2 * index, padx=(0, 4))
            entry.grid(row=0, column=2 * index + 1, padx=(0, 16))
            self.parameter_labels.append(label)
            self.parameter_entries.append(entry)
        self.hint = ttk.Label(self, padding=(14, 5), wraplength=1050)
        self.hint.pack(fill="x")

    def _build_result_list(self, parent):
        # Список результатов для сравнения.
        frame = ttk.Frame(parent)
        frame.pack(side="left", fill="y", padx=(0, 10))
        ttk.Label(frame, text="Результаты для сравнения").pack(anchor="w")
        self.result_list = tk.Listbox(frame, width=38, exportselection=False)
        self.result_list.pack(side="left", fill="y")
        # Щелчок по варианту сразу меняет предпросмотр.
        self.result_list.bind("<<ListboxSelect>>", lambda event: self._show_selected())
        scrollbar = ttk.Scrollbar(frame, command=self.result_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.result_list.configure(yscrollcommand=scrollbar.set)

    def _build_preview(self, parent):
        # Три области: исходник, результат и карта разности.
        frame = ttk.Frame(parent)
        frame.pack(side="left", fill="both", expand=True)
        self.preview_labels = []
        for index, title in enumerate(("Исходное", "Результат", "Разность |I - результат|")):
            panel = ttk.LabelFrame(frame, text=title, padding=6)
            panel.grid(row=0, column=index, sticky="nsew", padx=3)
            label = ttk.Label(panel, text="—")
            label.pack(expand=True)
            self.preview_labels.append(label)
            # Все три области одинаково расширяются вместе с окном.
            frame.columnconfigure(index, weight=1)
        frame.rowconfigure(0, weight=1)

    # Параметры -------------------------------------------------------------

    def _change_mode(self):
        # Обновить операции при смене пункта задания.
        names = MODES[self.mode.get()]
        self.operations.configure(values=names)
        # При смене пункта выбираем первую операцию и её параметры.
        self.operation.set(names[0])
        self._change_operation()

    def _change_operation(self):
        # Подписать поля и установить значения из lab_actions.FIELDS.
        mode, operation = self.mode.get(), self.operation.get()
        fields = FIELDS[(mode, operation)]
        for index, (label, entry) in enumerate(zip(self.parameter_labels, self.parameter_entries)):
            # Лишнее поле прячем, но не удаляем: оно понадобится другой операции.
            if index >= len(fields):
                label.grid_remove()
                entry.grid_remove()
                continue
            caption, default, _ = fields[index]
            label.configure(text=caption)
            entry.delete(0, "end")
            entry.insert(0, default)
            label.grid()
            entry.grid()
        hint = HINTS[mode]
        if operation == "Все фильтры":
            hint += " k=1,2; для сигма-фильтра k=2,3."
        self.hint.configure(text=hint)

    def _read_parameters(self):
        # Прочитать поля как списки чисел нужного типа.
        fields = FIELDS[(self.mode.get(), self.operation.get())]
        parameters = []
        # Тип int или float берём из таблицы полей, а не угадываем по тексту.
        for index, (_, _, number_type) in enumerate(fields):
            text = self.parameter_entries[index].get()
            # Запись "3,5" превращается в два варианта для сравнения.
            parts = [part.strip() for part in text.split(",")]
            if len(parts) > 10 or any(not part for part in parts):
                raise ValueError("Укажите от 1 до 10 значений через запятую.")
            values = [number_type(part) for part in parts]
            if any(isinstance(value, float) and not math.isfinite(value) for value in values):
                raise ValueError("Параметры должны быть конечными числами.")
            parameters.append(values)
        return parameters

    # Работа с изображением -------------------------------------------------

    def _open(self):
        # Открыть диалог выбора изображения.
        path = filedialog.askopenfilename(title="Выберите изображение")
        if path:
            self._load(path)

    def _load(self, path):
        # Загрузить исходник и очистить результаты прошлого изображения.
        try:
            # После convert("L") изображение не зависит от закрытого файла.
            with Image.open(path) as source:
                self.source = source.convert("L")
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка открытия", str(error))
            return
        # Старые результаты относятся к другому исходнику, поэтому убираем их.
        self.results.clear()
        self.result_list.delete(0, "end")
        self.status.set(f"Открыто: {Path(path).name}, {self.source.width}×{self.source.height}, 8 бит.")
        self._show_images(self.source, None, None)

    def _apply(self):
        # Запустить операцию и добавить результаты в список.
        if self.source is None:
            messagebox.showinfo("Изображение", "Сначала откройте изображение.")
            return
        self.status.set("Вычисление результатов...")
        # Показываем статус до обработки: несколько фильтров могут считаться секунды.
        self.update_idletasks()
        try:
            # lab_actions связывает выбор в окне с функциями из color/smoothing/sharpness.
            variants = make_variants(
                self.source, self.mode.get(), self.operation.get(), self._read_parameters()
            )
            self._add_results(variants)
        except (ValueError, OSError, OverflowError) as error:
            self.status.set("Проверьте параметры и повторите.")
            messagebox.showerror("Параметры", str(error))

    def _add_results(self, variants):
        # Запомнить варианты и выбрать последний.
        # Полные результаты остаются в памяти: можно переключаться без пересчёта.
        for title, image in variants:
            self.results.append((title, image))
            self.result_list.insert("end", title)
        last = len(self.results) - 1
        # Выделяем новый вариант, чтобы пользователь сразу увидел его справа.
        self.result_list.selection_clear(0, "end")
        self.result_list.selection_set(last)
        self.result_list.see(last)
        self._show_selected()
        self.status.set(f"Добавлено {len(variants)} вариантов. Всего: {len(self.results)}.")

    def _show_selected(self):
        # Показать выбранный результат и разность с исходником.
        selected = self.result_list.curselection()
        if selected:
            result = self.results[selected[0]][1]
            # Карту строим для выбранного результата, а не для всех вариантов сразу.
            difference = absolute_difference(self.source, result)
            self._show_images(self.source, result, difference)

    def _show_images(self, source, result, difference):
        # Показывать миниатюры; полные изображения не менять.
        self.preview_images.clear()
        for label, image in zip(self.preview_labels, (source, result, difference)):
            if image is None:
                label.configure(image="", text="—")
                continue
            # Уменьшаем только копию для экрана; сохранение берёт полный результат.
            preview = image.copy()
            preview.thumbnail((240, 430), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            # Без этой ссылки Tkinter может убрать изображение при очистке памяти.
            self.preview_images.append(photo)
            label.configure(image=photo, text="")

    def _save(self):
        # Сохранить выбранное полное изображение как PNG.
        selected = self.result_list.curselection()
        if not selected:
            messagebox.showinfo("Результат", "Сначала выберите результат в списке.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            initialdir=Path(__file__).resolve().parent,
            initialfile="result.png",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
        )
        if path:
            try:
                # Сохраняем полное изображение из results, а не уменьшенный предпросмотр.
                self.results[selected[0]][1].save(path)
                self.status.set(f"Сохранено: {path}")
            except OSError as error:
                messagebox.showerror("Ошибка сохранения", str(error))
