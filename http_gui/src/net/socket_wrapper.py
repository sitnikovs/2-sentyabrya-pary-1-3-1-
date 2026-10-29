import socket


class Socket:
    def __init__(self, sock: socket.socket):
        self._sock = sock

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def send_all(self, data: bytes):
        self._sock.sendall(data)

    def recv(self, n: int) -> bytes:
        return self._sock.recv(n)

    def settimeout(self, seconds: float):
        self._sock.settimeout(seconds)
