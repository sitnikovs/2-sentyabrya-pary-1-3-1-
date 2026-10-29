import logging
import queue
import socket
import threading
import time

from ..http.parser import MAX_HEADER_SIZE, Parser
from ..http.response import Response
from ..http.serializer import Serializer
from ..http.url import ParseError
from ..net.tcp_server import TcpServer
from . import handlers
from .router import Router

LOG = logging.getLogger(__name__)
MAX_BODY_SIZE = 10 * 1024 * 1024


class GuiQueueLogHandler(logging.Handler):
    """Send structured request log records to the GUI queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        entry = getattr(record, "request_entry", None)
        if entry is not None:
            self.log_queue.put(entry)


class HttpServer:
    """Small HTTP/1.x server intended for educational use."""

    def __init__(self, host="127.0.0.1", port=8080, log_queue=None):
        self.host = host
        self.port = port
        self.log_queue = log_queue or queue.Queue()
        self._gui_log_handler = GuiQueueLogHandler(self.log_queue)
        self.router = Router()
        self.router.route("GET", "/", handlers.hello)
        self.router.route("POST", "/echo", handlers.echo)
        self.router.route("GET", "/time", handlers.current_time)
        self.router.route("GET", "/headers", handlers.headers)
        self.parser = Parser()
        self.serializer = Serializer()
        self._tcp_server = None
        self._thread = None
        self._stop = threading.Event()
        self._workers = set()
        self._connections = set()
        self._lock = threading.Lock()

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        tcp_server = TcpServer(self.host, self.port)
        tcp_server.start(timeout=0.2)
        self.port = tcp_server.port
        self._tcp_server = tcp_server
        self._thread = threading.Thread(
            target=self._serve,
            args=(tcp_server,),
            name="http-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._tcp_server:
            self._tcp_server.close()
            self._tcp_server = None
        with self._lock:
            workers = list(self._workers)
            connections = list(self._connections)
        for conn in connections:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None
        for worker in workers:
            worker.join(timeout=2)

    def _serve(self, tcp_server):
        while not self._stop.is_set():
            try:
                conn, addr = tcp_server.accept()
            except socket.timeout:
                continue
            except (OSError, RuntimeError):
                break
            if self._stop.is_set():
                conn.close()
                break
            worker = threading.Thread(
                target=self._handle,
                args=(conn, addr),
                daemon=True,
            )
            with self._lock:
                self._workers.add(worker)
                self._connections.add(conn)
            worker.start()

    def _handle(self, conn, _addr):
        buffer = bytearray()
        try:
            with conn:
                conn.settimeout(2)
                while not self._stop.is_set():
                    started = time.perf_counter()
                    method, path, status = "?", "?", 400
                    try:
                        raw, buffer = self._read_one_request(conn, buffer)
                        if raw is None:
                            break
                        req = self.parser.parse_request(raw)
                        method, path = req.method, req.path
                        response = self.router.dispatch(req)
                        keep_alive = self._should_keep_alive(req)
                        response.headers = dict(response.headers)
                        response.headers["Connection"] = (
                            "keep-alive" if keep_alive else "close"
                        )
                    except ParseError as exc:
                        response = Response(
                            400,
                            "Bad Request",
                            headers={
                                "Content-Type": "text/plain; charset=utf-8",
                                "Connection": "close",
                            },
                            body=str(exc).encode("utf-8", errors="replace"),
                        )
                        keep_alive = False
                    status = response.status
                    conn.sendall(self.serializer.serialize_response(response))
                    self._log_request(method, path, status, started)
                    if not keep_alive:
                        break
        except (OSError, TimeoutError) as exc:
            LOG.debug("Connection error: %s", exc)
        finally:
            current = threading.current_thread()
            with self._lock:
                self._workers.discard(current)
                self._connections.discard(conn)

    def _log_request(self, method, path, status, started):
        elapsed = (time.perf_counter() - started) * 1000
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "method": method,
            "path": path,
            "status": status,
            "ms": round(elapsed, 2),
        }
        record = LOG.makeRecord(
            LOG.name,
            logging.INFO,
            __file__,
            0,
            "%s %s -> %s %.2fms",
            (method, path, status, elapsed),
            None,
            extra={"request_entry": entry},
        )
        self._gui_log_handler.handle(record)
        LOG.handle(record)

    @staticmethod
    def _should_keep_alive(req):
        connection = ""
        for key, value in req.headers.items():
            if key.lower() == "connection":
                connection = {token.strip().lower() for token in value.split(",")}
                break
        if req.version == "HTTP/1.1":
            return "close" not in connection
        return "keep-alive" in connection and "close" not in connection

    @staticmethod
    def _read_one_request(conn, buffer):
        data = bytearray(buffer)
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                if not data:
                    return None, bytearray()
                break
            data.extend(chunk)
            marker = data.find(b"\r\n\r\n")
            if marker > MAX_HEADER_SIZE or marker < 0 and len(data) > MAX_HEADER_SIZE + 3:
                raise ParseError("Headers too large")

        marker = data.find(b"\r\n\r\n")
        if marker < 0:
            raise ParseError("Incomplete HTTP headers")
        if marker > MAX_HEADER_SIZE:
            raise ParseError("Headers too large")

        head = bytes(data[: marker + 4])
        _, headers, _ = Parser.split_headers(head)
        length = Parser.content_length(headers) or 0
        if length > MAX_BODY_SIZE:
            raise ParseError("Request body exceeds 10 MiB")
        if Parser.transfer_encoding(headers):
            raise ParseError("Chunked request bodies are not supported")

        target = marker + 4 + length
        while len(data) < target:
            chunk = conn.recv(min(4096, target - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) < target:
            raise ParseError("Incomplete request body")
        return bytes(data[:target]), bytearray(data[target:])
