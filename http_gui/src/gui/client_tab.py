import json
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk

from ..client.http_client import HttpClient
from .widgets import HeaderTable


class ClientTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.client = HttpClient()
        self.result_queue = queue.Queue()

        top = ttk.Frame(self)
        top.pack(fill="x")
        self.method = ttk.Combobox(
            top,
            values=("GET", "POST"),
            state="readonly",
            width=8,
        )
        self.method.set("GET")
        self.method.pack(side="left")
        self.method.bind("<<ComboboxSelected>>", self._method_changed)

        self.url = ttk.Entry(top)
        self.url.insert(0, "http://localhost:8080/")
        self.url.pack(side="left", fill="x", expand=True, padx=5)
        self.url.bind("<Return>", lambda _event: self.send_request())

        self.send_btn = ttk.Button(
            top,
            text="Отправить",
            command=self.send_request,
        )
        self.send_btn.pack(side="left")
        ttk.Button(top, text="Очистить", command=self.clear).pack(
            side="left",
            padx=(5, 0),
        )

        ttk.Label(self, text="Заголовки").pack(anchor="w", pady=(8, 0))
        self.headers = HeaderTable(self)
        self.headers.pack(fill="x")

        ttk.Label(self, text="Тело запроса").pack(anchor="w", pady=(8, 0))
        self.body = tk.Text(self, height=6, wrap="word")
        self.body.pack(fill="x")
        self.body.config(state="disabled")

        self.status = ttk.Label(self, text="Готово")
        self.status.pack(anchor="w", pady=(8, 0))

        response_frame = ttk.Frame(self)
        response_frame.pack(fill="both", expand=True)
        self.response = tk.Text(response_frame, height=18, wrap="none")
        vertical = ttk.Scrollbar(
            response_frame,
            orient="vertical",
            command=self.response.yview,
        )
        horizontal = ttk.Scrollbar(
            response_frame,
            orient="horizontal",
            command=self.response.xview,
        )
        self.response.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        self.response.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        response_frame.rowconfigure(0, weight=1)
        response_frame.columnconfigure(0, weight=1)

        # Distinct, readable highlighting. The response is still plain text,
        # tags only affect presentation and never alter received bytes.
        self.response.tag_configure(
            "status_ok",
            foreground="#16833b",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.response.tag_configure(
            "status_redirect",
            foreground="#9a6700",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.response.tag_configure(
            "status_error",
            foreground="#c62828",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.response.tag_configure("header_name", foreground="#5e35b1")
        self.response.tag_configure(
            "json_key",
            foreground="#1565c0",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.response.tag_configure("json_string", foreground="#2e7d32")
        self.response.tag_configure("json_number", foreground="#ad1457")
        self.response.tag_configure("json_literal", foreground="#7b1fa2")
        self.response.tag_configure("html_tag", foreground="#1565c0")
        self.response.tag_configure("html_attr", foreground="#7b1fa2")
        self.response.tag_configure("html_string", foreground="#2e7d32")
        self.response.tag_configure("error_text", foreground="#c62828")
        self.response.config(state="disabled")

        self.after(100, self._poll_results)

    def _method_changed(self, _event=None):
        state = "normal" if self.method.get() == "POST" else "disabled"
        self.body.config(state=state)

    def clear(self):
        previous = self.body.cget("state")
        self.body.config(state="normal")
        self.body.delete("1.0", "end")
        self.body.config(state=previous)
        self._replace_response("")
        self.status.config(text="Готово")

    def send_request(self):
        url = self.url.get().strip()
        method = self.method.get()
        if not url:
            self._show("ValueError: URL не может быть пустым", "Ошибка")
            return
        try:
            headers = self.headers.values()
            body = self.body.get("1.0", "end-1c") if method == "POST" else ""
        except ValueError as exc:
            self._show(f"ValueError: {exc}", "Ошибка")
            return

        self.send_btn.config(state="disabled")
        self.status.config(text="Отправка...")
        threading.Thread(
            target=self._worker,
            args=(method, url, headers, body),
            daemon=True,
        ).start()

    def _worker(self, method, url, headers, body):
        try:
            if method == "POST":
                content_type = headers.get(
                    "Content-Type",
                    "text/plain; charset=utf-8",
                )
                response = self.client.post(url, body, content_type, headers)
            else:
                response = self.client.get(url, headers)

            text = response.body.decode("utf-8", errors="replace")
            content_type = next(
                (
                    value
                    for key, value in response.headers.items()
                    if key.lower() == "content-type"
                ),
                "",
            )
            if "json" in content_type:
                try:
                    text = json.dumps(
                        json.loads(text),
                        ensure_ascii=False,
                        indent=2,
                    )
                except json.JSONDecodeError:
                    pass

            header_text = "\n".join(
                f"{key}: {value}" for key, value in response.headers.items()
            )
            output = (
                f"{response.version} {response.status} {response.reason}\n"
                f"{header_text}\n\n{text}"
            )
            self.result_queue.put(
                (
                    output,
                    f"Статус: {response.status} {response.reason}",
                    content_type,
                    response.status,
                )
            )
        except Exception as exc:  # worker boundary: transfer error to GUI
            self.result_queue.put(
                (f"{type(exc).__name__}: {exc}", "Ошибка", "", None)
            )

    def _poll_results(self):
        try:
            while True:
                text, status, content_type, status_code = (
                    self.result_queue.get_nowait()
                )
                self._show(text, status, content_type, status_code)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_results)

    def _show(self, text, status, content_type="", status_code=None):
        self._replace_response(text)

        if status_code is None:
            self.response.tag_add("error_text", "1.0", "end-1c")
        else:
            status_tag = self._status_tag(status_code)
            self.response.tag_add(status_tag, "1.0", "1.end")
            self._highlight_headers(text)
            if "json" in content_type.lower():
                self._highlight_json(text)
            elif "html" in content_type.lower():
                self._highlight_html(text)

        self.response.config(state="disabled")
        self.status.config(text=status)
        self.send_btn.config(state="normal")

    def _replace_response(self, text):
        self.response.config(state="normal")
        self.response.delete("1.0", "end")
        if text:
            self.response.insert("1.0", text)
        self.response.config(state="disabled")

    @staticmethod
    def _status_tag(status_code):
        if 200 <= status_code < 300:
            return "status_ok"
        if 300 <= status_code < 400:
            return "status_redirect"
        return "status_error"

    def _highlight_headers(self, text):
        header_end = text.find("\n\n")
        if header_end < 0:
            return
        for match in re.finditer(r"(?m)^([^\s:][^:]*):(?=\s)", text[:header_end]):
            self._tag_offsets(
                "header_name",
                text,
                match.start(1),
                match.end(1),
            )

    def _highlight_json(self, text):
        body_start = text.find("\n\n")
        if body_start < 0:
            return
        offset = body_start + 2
        body = text[offset:]

        # Strings first, then override key strings with the stronger key tag.
        for match in re.finditer(r'"(?:\\.|[^"\\])*"', body):
            self._tag_offsets(
                "json_string",
                text,
                offset + match.start(),
                offset + match.end(),
            )
        for match in re.finditer(r'(?m)^\s*("(?:\\.|[^"\\])*")(?=\s*:)', body):
            self._tag_offsets(
                "json_key",
                text,
                offset + match.start(1),
                offset + match.end(1),
            )
        for match in re.finditer(
            r"(?<![\w.])-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?",
            body,
        ):
            self._tag_offsets(
                "json_number",
                text,
                offset + match.start(),
                offset + match.end(),
            )
        for match in re.finditer(r"\b(?:true|false|null)\b", body):
            self._tag_offsets(
                "json_literal",
                text,
                offset + match.start(),
                offset + match.end(),
            )

    def _highlight_html(self, text):
        body_start = text.find("\n\n")
        if body_start < 0:
            return
        offset = body_start + 2
        body = text[offset:]
        for match in re.finditer(r"</?[^>]+>", body):
            tag_start = offset + match.start()
            tag_end = offset + match.end()
            self._tag_offsets("html_tag", text, tag_start, tag_end)

            fragment = match.group(0)
            for attr in re.finditer(
                r"\s([A-Za-z_:][-A-Za-z0-9_:.]*)(?=\s*=)",
                fragment,
            ):
                self._tag_offsets(
                    "html_attr",
                    text,
                    tag_start + attr.start(1),
                    tag_start + attr.end(1),
                )
            for value in re.finditer(r"=(\"[^\"]*\"|'[^']*')", fragment):
                self._tag_offsets(
                    "html_string",
                    text,
                    tag_start + value.start(1),
                    tag_start + value.end(1),
                )

    def _tag_offsets(self, tag, text, start, end):
        start_line = text.count("\n", 0, start) + 1
        start_col = start - (text.rfind("\n", 0, start) + 1)
        end_line = text.count("\n", 0, end) + 1
        end_col = end - (text.rfind("\n", 0, end) + 1)
        self.response.tag_add(
            tag,
            f"{start_line}.{start_col}",
            f"{end_line}.{end_col}",
        )
