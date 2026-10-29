import re

from .interfaces import HttpParser
from .request import Request
from .response import Response
from .url import ParseError

MAX_HEADER_SIZE = 8192
TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class Parser(HttpParser):
    @staticmethod
    def split_headers(data: bytes):
        marker = data.find(b"\r\n\r\n")
        if marker < 0:
            raise ParseError("Incomplete HTTP headers")
        if marker > MAX_HEADER_SIZE:
            raise ParseError("HTTP headers exceed 8 KiB")
        try:
            head = data[:marker].decode("iso-8859-1")
        except UnicodeDecodeError as exc:
            raise ParseError("Invalid header encoding") from exc
        lines = head.split("\r\n")
        headers = {}
        for line in lines[1:]:
            if not line or ":" not in line:
                raise ParseError("Malformed header")
            name, value = line.split(":", 1)
            if not TOKEN.fullmatch(name):
                raise ParseError("Invalid header name")
            if any(ord(char) < 32 and char != "\t" or ord(char) == 127 for char in value):
                raise ParseError("Invalid header value")
            existing = next((key for key in headers if key.lower() == name.lower()), None)
            if existing is not None:
                if name.lower() in {"host", "content-length", "transfer-encoding"}:
                    raise ParseError("Duplicate framing or Host header")
                headers[existing] += ", " + value.strip()
            else:
                headers[name] = value.strip()
        return lines[0], headers, data[marker + 4:]

    def parse_request(self, data: bytes) -> Request:
        first, headers, body = self.split_headers(data)
        parts = first.split(" ")
        if len(parts) != 3 or parts[2] not in {"HTTP/1.0", "HTTP/1.1"}:
            raise ParseError("Malformed request line")
        method, path, version = parts
        if not TOKEN.fullmatch(method) or not path.startswith("/") or any(ord(char) <= 32 for char in path):
            raise ParseError("Invalid method or request target")
        if version == "HTTP/1.1" and not self._get(headers, "Host"):
            raise ParseError("Host header is required for HTTP/1.1")
        length = self.content_length(headers)
        if self.transfer_encoding(headers):
            raise ParseError("Chunked request bodies are not supported")
        if length is not None:
            if len(body) < length:
                raise ParseError("Incomplete request body")
            body = body[:length]
        return Request(method, path, version, headers, body)

    def parse_response(self, data: bytes) -> Response:
        first, headers, body = self.split_headers(data)
        parts = first.split(" ", 2)
        if len(parts) < 2 or parts[0] not in {"HTTP/1.0", "HTTP/1.1"}:
            raise ParseError("Malformed status line")
        try:
            status = int(parts[1])
        except ValueError as exc:
            raise ParseError("Invalid status code") from exc
        if not re.fullmatch(r"[1-5][0-9]{2}", parts[1]):
            raise ParseError("Invalid status code")
        reason = parts[2] if len(parts) == 3 else ""
        length = self.content_length(headers)
        encoding = self.transfer_encoding(headers)
        if status < 200 or status in {204, 304}:
            body = b""
        elif encoding:
            body = self.decode_chunked(body)
        else:
            if length is not None:
                if len(body) < length:
                    raise ParseError("Incomplete response body")
                body = body[:length]
        return Response(status, reason, parts[0], headers, body)

    @staticmethod
    def _get(headers, name):
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return ""

    @classmethod
    def content_length(cls, headers):
        raw = cls._get(headers, "Content-Length")
        if not any(key.lower() == "content-length" for key in headers):
            return None
        if not re.fullmatch(r"[0-9]+", raw):
            raise ParseError("Invalid Content-Length")
        return int(raw)

    @classmethod
    def transfer_encoding(cls, headers):
        if not any(key.lower() == "transfer-encoding" for key in headers):
            return ""
        if any(key.lower() == "content-length" for key in headers):
            raise ParseError("Content-Length and Transfer-Encoding cannot be used together")
        value = cls._get(headers, "Transfer-Encoding").lower()
        if value != "chunked":
            raise ParseError("Unsupported Transfer-Encoding")
        return value

    @staticmethod
    def chunked_end(data: bytes):
        """Return the framed body's end, or None when more bytes are required."""
        pos = 0
        while True:
            end = data.find(b"\r\n", pos)
            if end < 0:
                if len(data) - pos > MAX_HEADER_SIZE:
                    raise ParseError("Chunk header exceeds 8 KiB")
                return None
            size_text = data[pos:end].split(b";", 1)[0]
            if end - pos > MAX_HEADER_SIZE or not re.fullmatch(rb"[0-9a-fA-F]+", size_text):
                raise ParseError("Invalid chunk size")
            size = int(size_text, 16)
            pos = end + 2
            if size == 0:
                trailer_start = pos
                while True:
                    end = data.find(b"\r\n", pos)
                    if end < 0:
                        if len(data) - trailer_start > MAX_HEADER_SIZE:
                            raise ParseError("Trailers exceed 8 KiB")
                        return None
                    if end - trailer_start > MAX_HEADER_SIZE:
                        raise ParseError("Trailers exceed 8 KiB")
                    if end == pos:
                        return end + 2
                    line = data[pos:end]
                    if b":" not in line:
                        raise ParseError("Malformed trailer")
                    name = line.split(b":", 1)[0].decode("iso-8859-1")
                    if not TOKEN.fullmatch(name) or name.lower() in {"content-length", "transfer-encoding", "host"}:
                        raise ParseError("Invalid trailer")
                    pos = end + 2
            if len(data) < pos + size + 2:
                return None
            if data[pos + size:pos + size + 2] != b"\r\n":
                raise ParseError("Malformed chunk")
            pos += size + 2

    @classmethod
    def decode_chunked(cls, data: bytes) -> bytes:
        if cls.chunked_end(data) is None:
            raise ParseError("Incomplete chunked body")
        result = bytearray()
        pos = 0
        while True:
            end = data.find(b"\r\n", pos)
            size = int(data[pos:end].split(b";", 1)[0], 16)
            pos = end + 2
            if size == 0:
                return bytes(result)
            result.extend(data[pos:pos + size])
            pos += size + 2
