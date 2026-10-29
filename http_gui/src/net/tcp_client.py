import socket
import ssl
from .socket_wrapper import Socket


class TcpClient:
    def connect(self, host: str, port: int, timeout: float, use_ssl: bool = False) -> Socket:
        raw = None
        try:
            raw = socket.create_connection((host, port), timeout=timeout)
            raw.settimeout(timeout)
            if use_ssl:
                raw = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
            return Socket(raw)
        except socket.timeout as exc:
            if raw is not None:
                raw.close()
            raise TimeoutError("Connection timed out") from exc
        except OSError as exc:
            if raw is not None:
                raw.close()
            raise ConnectionError(str(exc)) from exc
