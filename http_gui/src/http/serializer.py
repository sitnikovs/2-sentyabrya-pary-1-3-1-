from email.utils import formatdate
from http import HTTPStatus
from .interfaces import HttpSerializer
from .parser import Parser, TOKEN
from .request import Request
from .response import Response
from .url import ParseError


class Serializer(HttpSerializer):
    @staticmethod
    def _headers(headers):
        seen = set()
        for name, value in headers.items():
            if not isinstance(name, str) or not TOKEN.fullmatch(name):
                raise ParseError("Invalid header name")
            if not isinstance(value, str) or any(ord(char) < 32 and char != "\t" or ord(char) == 127 for char in value):
                raise ParseError("Invalid header value")
            if name.lower() in seen:
                raise ParseError("Duplicate header name")
            seen.add(name.lower())
        try:
            return "".join(f"{k}: {v}\r\n" for k, v in headers.items()).encode("iso-8859-1")
        except UnicodeEncodeError as exc:
            raise ParseError("HTTP headers must use ISO-8859-1 characters") from exc

    def serialize_request(self, request: Request) -> bytes:
        headers = dict(request.headers)
        if self._has(headers, "Transfer-Encoding"):
            raise ParseError("Chunked request bodies are not supported")
        if (request.body or request.method == "POST") and not self._has(headers, "Content-Length"):
            headers["Content-Length"] = str(len(request.body))
        length = Parser.content_length(headers)
        if length is not None and length != len(request.body):
            raise ParseError("Content-Length does not match the request body")
        try:
            start = f"{request.method} {request.path} {request.version}\r\n".encode("ascii")
        except UnicodeEncodeError as exc:
            raise ParseError("URL path must be percent-encoded") from exc
        payload = start + self._headers(headers) + b"\r\n" + request.body
        Parser().parse_request(payload)
        return payload

    def serialize_response(self, response: Response) -> bytes:
        headers = dict(response.headers)
        body = b"" if response.status < 200 or response.status in {204, 304} else response.body
        if self._has(headers, "Transfer-Encoding"):
            raise ParseError("The server serializes Content-Length responses only")
        defaults = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(body)),
            "Date": formatdate(usegmt=True),
            "Connection": "close",
        }
        for name, value in defaults.items():
            if not self._has(headers, name):
                headers[name] = value
        if Parser.content_length(headers) != len(body):
            raise ParseError("Content-Length does not match the response body")
        reason = response.reason
        if not reason:
            try:
                reason = HTTPStatus(response.status).phrase
            except ValueError:
                reason = "Unknown"
        start = f"{response.version} {response.status} {reason}\r\n".encode("ascii")
        if "\r" in reason or "\n" in reason:
            raise ParseError("Invalid reason phrase")
        return start + self._headers(headers) + b"\r\n" + body

    @staticmethod
    def _has(headers, name):
        return any(k.lower() == name.lower() for k in headers)
