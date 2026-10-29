import socket
import threading

import pytest

from src.client.http_client import HttpClient
from src.http.url import ParseError
from src.net.tcp_client import TcpClient


def _one_shot_server(payload: bytes):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def serve():
        with listener:
            conn, _ = listener.accept()
            with conn:
                conn.recv(4096)
                conn.sendall(payload)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return port, thread


def test_set_timeout_ms():
    client = HttpClient()
    client.set_timeout(250)
    assert client.timeout == pytest.approx(0.25)


def test_set_timeout_rejects_non_positive():
    client = HttpClient()
    with pytest.raises(ValueError):
        client.set_timeout(0)


def test_follow_redirects_rejects_negative():
    with pytest.raises(ValueError):
        HttpClient().follow_redirects(-1)


def test_full_client_reads_chunked_response():
    payload = (
        b"HTTP/1.1 200 OK\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Content-Type: text/plain\r\n"
        b"Connection: close\r\n\r\n"
        b"4\r\nWiki\r\n"
        b"5\r\npedia\r\n"
        b"0\r\n\r\n"
    )
    port, thread = _one_shot_server(payload)
    response = HttpClient().get(f"http://127.0.0.1:{port}/")
    thread.join(timeout=2)
    assert response.status == 200
    assert response.body == b"Wikipedia"


def test_client_rejects_response_headers_over_8_kib():
    payload = (
        b"HTTP/1.1 200 OK\r\n"
        + b"X-Large: "
        + b"a" * 9000
        + b"\r\nContent-Length: 0\r\n\r\n"
    )
    port, thread = _one_shot_server(payload)
    with pytest.raises(ParseError):
        HttpClient().get(f"http://127.0.0.1:{port}/")
    thread.join(timeout=2)


def test_disabled_redirects_return_original_response():
    port, thread = _one_shot_server(b"HTTP/1.1 302 Found\r\nLocation: /other\r\nContent-Length: 0\r\n\r\n")
    response = HttpClient().get(f"http://127.0.0.1:{port}/")
    thread.join(timeout=2)
    assert response.status == 302


def test_constructor_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        HttpClient(timeout_ms=0)


class FragmentedSocket:
    """A deterministic transport for boundaries between recv calls."""

    def __init__(self, fragments):
        self.fragments = iter(fragments)

    def recv(self, _size):
        return next(self.fragments, b"")


def test_header_limit_excludes_bytes_of_the_body():
    head = b"HTTP/1.1 200 OK\r\nX-Padding: " + b"a" * 8000 + b"\r\nContent-Length: 1000\r\n\r\n"
    raw = head + b"x" * 1000
    client = HttpClient()
    result = client.parser.parse_response(client._read_response(FragmentedSocket([raw[:4096], raw[4096:]])))
    assert result.body == b"x" * 1000


def test_chunk_terminator_inside_data_is_not_end_of_message():
    head = b"HTTP/1.1 200 OK\r\nTransfer-Encoding:chunked\r\n\r\n"
    body = b"abc\r\n0\r\n\r\ndef"
    fragments = [head + b"d\r\n" + body[:10], body[10:] + b"\r\n0;last=yes\r\nX-End: yes\r\n\r\n"]
    client = HttpClient()
    response = client.parser.parse_response(client._read_response(FragmentedSocket(fragments)))
    assert response.body == body


def test_no_body_response_does_not_wait_for_close():
    class OpenSocket:
        def __init__(self):
            self.calls = 0

        def recv(self, _size):
            self.calls += 1
            if self.calls > 1:
                raise AssertionError("Must not recv a body for 204")
            return b"HTTP/1.1 204 No Content\r\nConnection: keep-alive\r\n\r\n"

    client = HttpClient()
    assert client.parser.parse_response(client._read_response(OpenSocket())).status == 204


def test_tls_failure_closes_the_created_socket(monkeypatch):
    class RawSocket:
        closed = False

        def settimeout(self, _timeout):
            pass

        def close(self):
            self.closed = True

    class FailingContext:
        def wrap_socket(self, _raw, server_hostname):
            raise OSError(f"TLS failed: {server_hostname}")

    raw = RawSocket()
    monkeypatch.setattr("src.net.tcp_client.socket.create_connection", lambda *_args, **_kwargs: raw)
    monkeypatch.setattr("src.net.tcp_client.ssl.create_default_context", FailingContext)
    with pytest.raises(ConnectionError):
        TcpClient().connect("example.com", 443, 1, use_ssl=True)
    assert raw.closed
