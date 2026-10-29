import socket


class TcpServer:
    """Owns the listening TCP socket used by HttpServer."""

    def __init__(self, host: str, port: int, backlog: int = 50):
        self.host = host
        self.port = port
        self.backlog = backlog
        self._sock = None

    def start(self, timeout: float = 0.2):
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
            sock.listen(self.backlog)
            sock.settimeout(timeout)
        except OSError:
            sock.close()
            raise
        self.port = sock.getsockname()[1]
        self._sock = sock

    def accept(self):
        sock = self._sock
        if sock is None:
            raise RuntimeError("TCP server is not started")
        return sock.accept()

    def close(self):
        if self._sock is None:
            return
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._sock.close()
        finally:
            self._sock = None
