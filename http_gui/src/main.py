from .gui.app import App, configure_logging


def main():
    configure_logging()
    App().mainloop()


if __name__ == "__main__":
    main()
