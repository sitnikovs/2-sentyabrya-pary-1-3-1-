import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from ..server.http_server import HttpServer
from .widgets import LogTable


class ServerTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.server = None
        self._busy = False
        self._close_callback = None

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Порт:").pack(side="left")
        self.port = ttk.Entry(top, width=8)
        self.port.insert(0, "8080")
        self.port.pack(side="left", padx=5)

        self.start_btn = ttk.Button(top, text="Запустить", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(
            top,
            text="Остановить",
            command=self.stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=5)
        self.browser_btn = ttk.Button(
            top,
            text="Открыть в браузере",
            command=self.open_browser,
        )
        self.browser_btn.pack(side="left")

        self.state = tk.Canvas(
            top,
            width=18,
            height=18,
            highlightthickness=0,
        )
        self.dot = self.state.create_oval(3, 3, 15, 15, fill="#c62828")
        self.state.pack(side="left", padx=(12, 4))
        self.state_label = ttk.Label(top, text="Сервер остановлен")
        self.state_label.pack(side="left")

        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=True, pady=10)
        self.log = LogTable(log_frame)
        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log.yview,
        )
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self,
            text="Очистить лог",
            command=self.clear_log,
        ).pack(anchor="e")
        self.after(100, self.poll)

    def start(self):
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом 1–65535")
            return

        if self._busy or (self.server and self.server.running):
            return

        self._busy = True
        self.start_btn.config(state="disabled")
        self.state_label.config(text="Запуск...")
        threading.Thread(target=self._start_worker, args=(port,), daemon=True).start()

    def _start_worker(self, port):
        server = HttpServer(port=port, log_queue=self.queue)
        try:
            server.start()
            self.result_queue.put(("started", server))
        except OSError as exc:
            self.result_queue.put(("start_error", str(exc)))

    def stop(self):
        if self._busy:
            return
        if not self.server or not self.server.running:
            self._set_running(False)
            if self._close_callback:
                self._close_callback()
            return
        self._busy = True
        self.stop_btn.config(state="disabled")
        self.state_label.config(text="Остановка...")
        threading.Thread(target=self._stop_worker, args=(self.server,), daemon=True).start()

    def _stop_worker(self, server):
        server.stop()
        self.result_queue.put(("stopped", None))

    def shutdown(self, callback):
        self._close_callback = callback
        if not self._busy:
            self.stop()

    def _set_running(self, running):
        if running:
            self.state.itemconfig(self.dot, fill="#16833b")
            self.state_label.config(text="Сервер запущен")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.port.config(state="disabled")
        else:
            self.state.itemconfig(self.dot, fill="#c62828")
            self.state_label.config(text="Сервер остановлен")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.port.config(state="normal")

    def open_browser(self):
        port = (
            self.server.port
            if self.server and self.server.running
            else self.port.get()
        )
        webbrowser.open(f"http://localhost:{port}/")

    def clear_log(self):
        self.log.delete(*self.log.get_children())

    def poll(self):
        try:
            while True:
                self.log.add(self.queue.get_nowait())
        except queue.Empty:
            pass
        try:
            while True:
                event, value = self.result_queue.get_nowait()
                self._busy = False
                if event == "started":
                    self.server = value
                    self.port.delete(0, "end")
                    self.port.insert(0, str(value.port))
                    self._set_running(True)
                    if self._close_callback:
                        self.stop()
                elif event == "start_error":
                    self._set_running(False)
                    if self._close_callback:
                        self._close_callback()
                    else:
                        messagebox.showerror("Ошибка запуска", value)
                else:
                    self.server = None
                    self._set_running(False)
                    if self._close_callback:
                        self._close_callback()
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self.poll)
