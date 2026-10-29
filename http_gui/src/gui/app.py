import logging
import tkinter as tk
from tkinter import ttk
from .client_tab import ClientTab
from .server_tab import ServerTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HTTP-клиент и сервер")
        self.geometry("950x720")
        notebook = ttk.Notebook(self)
        self.client_tab = ClientTab(notebook)
        self.server_tab = ServerTab(notebook)
        notebook.add(self.client_tab, text="Клиент")
        notebook.add(self.server_tab, text="Сервер")
        notebook.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        self.server_tab.shutdown(self.destroy)


def configure_logging():
    logging.basicConfig(filename="http_gui.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
