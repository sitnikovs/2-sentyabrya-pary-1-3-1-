import re
from tkinter import messagebox, ttk

HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class HeaderTable(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.tree = ttk.Treeview(
            self,
            columns=("name", "value"),
            show="headings",
            height=4,
        )
        self.tree.heading("name", text="Имя")
        self.tree.heading("value", text="Значение")
        self.tree.column("name", width=220)
        self.tree.column("value", width=520)
        self.tree.pack(fill="both", expand=True)

        row = ttk.Frame(self)
        row.pack(fill="x", pady=(4, 0))
        self.name = ttk.Entry(row)
        self.value = ttk.Entry(row)
        self.name.pack(side="left", fill="x", expand=True)
        self.value.pack(side="left", fill="x", expand=True, padx=(4, 4))
        self.value.bind("<Return>", lambda _event: self.add())
        ttk.Button(row, text="Добавить", command=self.add).pack(side="left")
        ttk.Button(row, text="Удалить", command=self.remove).pack(
            side="left",
            padx=(4, 0),
        )

    def add(self):
        name = self.name.get().strip()
        value = self.value.get().strip()
        if not name:
            messagebox.showerror("Ошибка заголовка", "Введите имя заголовка")
            return
        if not HEADER_NAME.fullmatch(name):
            messagebox.showerror(
                "Ошибка заголовка",
                "Имя содержит недопустимые символы для HTTP-заголовка",
            )
            return
        if "\r" in value or "\n" in value:
            messagebox.showerror(
                "Ошибка заголовка",
                "Значение заголовка не должно содержать перевод строки",
            )
            return

        self.tree.insert("", "end", values=(name, value))
        self.name.delete(0, "end")
        self.value.delete(0, "end")
        self.name.focus_set()

    def remove(self):
        for item in self.tree.selection():
            self.tree.delete(item)

    def values(self):
        result = {}
        for item in self.tree.get_children():
            name, value = self.tree.item(item, "values")
            if not HEADER_NAME.fullmatch(name) or "\r" in value or "\n" in value:
                raise ValueError(f"Некорректный HTTP-заголовок: {name}")
            result[name] = value
        return result


class LogTable(ttk.Treeview):
    def __init__(self, master):
        columns = ("time", "method", "path", "status", "ms")
        super().__init__(master, columns=columns, show="headings")
        titles = ("Время", "Метод", "Путь", "Статус", "мс")
        for col, title in zip(columns, titles):
            self.heading(col, text=title)
        self.column("time", width=90)
        self.column("method", width=70)
        self.column("path", width=260)
        self.column("status", width=70)
        self.column("ms", width=80)

        self.tag_configure("success", foreground="#16833b")
        self.tag_configure("redirect", foreground="#9a6700")
        self.tag_configure("error", foreground="#c62828")

    def add(self, item):
        keys = ("time", "method", "path", "status", "ms")
        status = int(item["status"])
        if 200 <= status < 300:
            tag = "success"
        elif 300 <= status < 400:
            tag = "redirect"
        else:
            tag = "error"
        self.insert(
            "",
            "end",
            values=tuple(item[key] for key in keys),
            tags=(tag,),
        )
        children = self.get_children()
        if children:
            self.see(children[-1])
