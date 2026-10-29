from dataclasses import dataclass
from urllib.parse import urlsplit


class ParseError(ValueError):
    """Raised when an HTTP message or URL cannot be parsed."""


@dataclass(frozen=True)
class Url:
    scheme: str
    host: str
    port: int
    path: str
    query: str = ""

    @classmethod
    def parse(cls, value: str) -> "Url":
        try:
            if not isinstance(value, str) or any(char.isspace() or ord(char) < 32 for char in value):
                raise ParseError("URL must not contain whitespace or control characters")
            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ParseError("URL must start with http:// or https:// and contain a host")
            try:
                port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
            except ValueError as exc:
                raise ParseError("Invalid port") from exc
            if not 1 <= port <= 65535:
                raise ParseError("Port must be in range 1..65535")
            path = parsed.path or "/"
            return cls(parsed.scheme, parsed.hostname, port, path, parsed.query)
        except ParseError:
            raise
        except (TypeError, ValueError) as exc:
            raise ParseError(str(exc)) from exc

    @property
    def target(self) -> str:
        return self.path + (("?" + self.query) if self.query else "")

    @property
    def host_header(self) -> str:
        default = (self.scheme == "http" and self.port == 80) or (self.scheme == "https" and self.port == 443)
        host = f"[{self.host}]" if ":" in self.host else self.host
        return host if default else f"{host}:{self.port}"
