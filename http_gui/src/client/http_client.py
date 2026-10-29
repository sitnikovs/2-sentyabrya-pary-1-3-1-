import socket
from urllib.parse import urljoin

from ..http.parser import MAX_HEADER_SIZE, Parser
from ..http.request import Request
from ..http.serializer import Serializer
from ..http.url import ParseError, Url
from ..net.tcp_client import TcpClient


class HttpError(Exception):
    def __init__(self, status: int, message: str = ""):
        super().__init__(message or f"HTTP error {status}")
        self.status = status


class HttpClient:
    REDIRECT_STATUSES = {301, 302, 303, 307, 308}

    def __init__(self, timeout_ms: int = 5000):
        self.set_timeout(timeout_ms)
        self.max_redirects = 0
        self.tcp = TcpClient()
        self.parser = Parser()
        self.serializer = Serializer()

    def set_timeout(self, ms: int):
        if ms <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = ms / 1000.0

    def follow_redirects(self, max_redirects: int):
        """Enable redirects up to max_redirects; 0 disables redirect following."""
        if max_redirects < 0:
            raise ValueError("max_redirects must be non-negative")
        self.max_redirects = max_redirects
        return self

    @staticmethod
    def raise_for_status(response):
        """Raise HttpError(status) for HTTP 4xx/5xx responses when desired."""
        if response.status >= 400:
            raise HttpError(response.status, f"HTTP error {response.status} {response.reason}")
        return response

    def get(self, url: str, headers=None):
        return self._request("GET", url, b"", None, headers)

    def post(self, url: str, body, content_type="text/plain", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        return self._request("POST", url, body, content_type, headers)

    def _request(self, method, url, body, content_type, headers):
        current_method = method
        current_url = url
        current_body = body
        current_content_type = content_type
        current_headers = dict(headers or {})

        for redirect_count in range(self.max_redirects + 1):
            response = self._request_once(
                current_method,
                current_url,
                current_body,
                current_content_type,
                current_headers,
            )
            if not self.max_redirects or response.status not in self.REDIRECT_STATUSES:
                return response

            location = self._header(response.headers, "Location")
            if not location:
                return response
            if redirect_count >= self.max_redirects:
                raise HttpError(response.status, "Maximum redirect count exceeded")

            next_url = urljoin(current_url, location)
            source, destination = Url.parse(current_url), Url.parse(next_url)
            if (source.scheme, source.host, source.port) != (destination.scheme, destination.host, destination.port):
                for name in ("Authorization", "Cookie", "Proxy-Authorization"):
                    self._remove_header(current_headers, name)
            current_url = next_url
            if response.status in {301, 302, 303} and current_method == "POST":
                current_method = "GET"
                current_body = b""
                current_content_type = None

        raise HttpError(310, "Too many redirects")

    def _request_once(self, method, url, body, content_type, headers):
        parsed = Url.parse(url)
        hdrs = dict(headers or {})
        self._set_header(hdrs, "Host", parsed.host_header)
        self._set_default_header(hdrs, "User-Agent", "SocketHTTPGUI/1.0")
        self._set_default_header(hdrs, "Accept", "*/*")
        self._set_default_header(hdrs, "Connection", "close")
        if content_type:
            self._set_default_header(hdrs, "Content-Type", content_type)
        elif method == "GET":
            self._remove_header(hdrs, "Content-Type")
            self._remove_header(hdrs, "Content-Length")

        req = Request(method, parsed.target, headers=hdrs, body=body)
        payload = self.serializer.serialize_request(req)
        with self.tcp.connect(
            parsed.host,
            parsed.port,
            self.timeout,
            parsed.scheme == "https",
        ) as sock:
            sock.send_all(payload)
            raw = self._read_response(sock)
        return self.parser.parse_response(raw)

    def _read_response(self, sock):
        data = bytearray()
        try:
            while b"\r\n\r\n" not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data.extend(chunk)
                marker = data.find(b"\r\n\r\n")
                if marker > MAX_HEADER_SIZE or marker < 0 and len(data) > MAX_HEADER_SIZE + 3:
                    raise ParseError("HTTP response headers exceed 8 KiB")

            marker = data.find(b"\r\n\r\n")
            if marker < 0:
                return bytes(data)
            head = bytes(data[: marker + 4])
            first, headers, _ = self.parser.split_headers(head)
            length = self.parser.content_length(headers)
            encoding = self.parser.transfer_encoding(headers)
            parts = first.split(" ", 2)
            if len(parts) >= 2 and (parts[1].startswith("1") or parts[1] in {"204", "304"}):
                return head
            if encoding:
                while self.parser.chunked_end(bytes(data[marker + 4:])) is None:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data.extend(chunk)
            else:
                if length is not None:
                    target = marker + 4 + length
                    while len(data) < target:
                        chunk = sock.recv(min(4096, target - len(data)))
                        if not chunk:
                            break
                        data.extend(chunk)
                else:
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        data.extend(chunk)
        except socket.timeout as exc:
            raise TimeoutError("Read timed out") from exc
        except OSError as exc:
            raise ConnectionError(str(exc)) from exc
        return bytes(data)

    @staticmethod
    def _header(headers, name):
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return ""

    @classmethod
    def _set_header(cls, headers, name, value):
        cls._remove_header(headers, name)
        headers[name] = value

    @staticmethod
    def _set_default_header(headers, name, value):
        if not any(key.lower() == name.lower() for key in headers):
            headers[name] = value

    @staticmethod
    def _remove_header(headers, name):
        for key in list(headers):
            if key.lower() == name.lower():
                del headers[key]
