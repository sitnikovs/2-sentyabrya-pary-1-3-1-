import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.client.http_client import HttpClient
from src.server.http_server import HttpServer


@pytest.fixture
def server():
    srv = HttpServer(port=0)
    srv.start()
    yield srv
    srv.stop()


def url(server, path="/"):
    return f"http://127.0.0.1:{server.port}{path}"


def test_get_hello(server):
    response = HttpClient().get(url(server))
    assert response.status == 200 and b"Hello" in response.body


def test_post_echo(server):
    response = HttpClient().post(url(server, "/echo"), b"abc", "text/plain")
    assert response.status == 200
    assert response.body == b"abc"
    assert response.headers["Content-Type"] == "text/plain"


def test_status_404(server):
    assert HttpClient().get(url(server, "/status/404")).status == 404


def test_nonexistent(server):
    assert HttpClient().get(url(server, "/nonexistent")).status == 404


def test_100_sequential(server):
    client = HttpClient()
    assert all(client.get(url(server)).status == 200 for _ in range(100))


def test_parallel(server):
    def one(_):
        return HttpClient().get(url(server)).status

    with ThreadPoolExecutor(max_workers=10) as pool:
        assert list(pool.map(one, range(10))) == [200] * 10


def test_timeout_100_ms():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def slow_server():
        with listener:
            conn, _ = listener.accept()
            with conn:
                conn.recv(4096)
                time.sleep(1)

    thread = threading.Thread(target=slow_server, daemon=True)
    thread.start()
    client = HttpClient(timeout_ms=100)
    with pytest.raises(TimeoutError):
        client.get(f"http://127.0.0.1:{port}/")
    thread.join(timeout=2)


def test_garbage_returns_400_and_server_survives(server):
    with socket.create_connection(("127.0.0.1", server.port), timeout=2) as sock:
        sock.sendall(b"garbage\r\n\r\n")
        data = sock.recv(4096)
    assert b" 400 " in data
    assert HttpClient().get(url(server)).status == 200


def test_keep_alive_three_requests(server):
    with socket.create_connection(("127.0.0.1", server.port), timeout=2) as sock:
        sock.settimeout(2)
        for index in range(3):
            connection = "close" if index == 2 else "keep-alive"
            request = (
                "GET / HTTP/1.1\r\n"
                "Host: localhost\r\n"
                f"Connection: {connection}\r\n\r\n"
            ).encode("ascii")
            sock.sendall(request)
            response = _recv_response(sock)
            assert b"HTTP/1.1 200 OK" in response
            assert b"Hello" in response


def _recv_response(sock):
    data = bytearray()
    while b"\r\n\r\n" not in data:
        data.extend(sock.recv(4096))
    marker = data.find(b"\r\n\r\n")
    header = bytes(data[:marker])
    length = 0
    for line in header.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1].strip())
    target = marker + 4 + length
    while len(data) < target:
        data.extend(sock.recv(target - len(data)))
    return bytes(data[:target])


def test_1000_requests(server):
    client = HttpClient()
    for _ in range(1000):
        assert client.get(url(server)).status == 200

    deadline = time.time() + 2
    while time.time() < deadline:
        with server._lock:
            if not server._workers:
                break
        time.sleep(0.01)
    with server._lock:
        assert not server._workers


def test_time_json(server):
    response = HttpClient().get(url(server, "/time"))
    assert response.status == 200 and b'"time"' in response.body


def test_headers_route(server):
    response = HttpClient().get(url(server, "/headers"), {"X-Test": "yes"})
    assert response.status == 200 and b"X-Test" in response.body


def test_port_freed_after_stop():
    srv = HttpServer(port=0)
    srv.start()
    port = srv.port
    srv.stop()
    other = HttpServer(port=port)
    other.start()
    other.stop()


def test_follow_redirects_bonus(server):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    redirect_port = listener.getsockname()[1]

    def redirect_server():
        with listener:
            conn, _ = listener.accept()
            with conn:
                conn.recv(4096)
                location = url(server, "/")
                payload = (
                    "HTTP/1.1 302 Found\r\n"
                    f"Location: {location}\r\n"
                    "Content-Length: 0\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii")
                conn.sendall(payload)

    thread = threading.Thread(target=redirect_server, daemon=True)
    thread.start()
    client = HttpClient().follow_redirects(2)
    response = client.get(f"http://127.0.0.1:{redirect_port}/redirect")
    thread.join(timeout=2)
    assert response.status == 200
    assert b"Hello" in response.body


def test_raise_for_status_uses_http_error(server):
    from src.client.http_client import HttpError

    response = HttpClient().get(url(server, "/status/418"))
    with pytest.raises(HttpError) as error:
        HttpClient.raise_for_status(response)
    assert error.value.status == 418


def test_large_post_with_legal_large_header(server):
    body = b"x" * 12000
    response = HttpClient().post(url(server, "/echo"), body, "text/plain", {"X-Padding": "a" * 7800})
    assert response.status == 200 and response.body == body


@pytest.mark.parametrize("headers", [
    b"Content-Length: 0\r\ncontent-length: 4",
    b"Content-Length: 0\r\nTransfer-Encoding: chunked",
    b"Content-Length : 0",
])
def test_ambiguous_framing_is_400(server, headers):
    with socket.create_connection(("127.0.0.1", server.port), timeout=2) as sock:
        sock.sendall(b"POST /echo HTTP/1.1\r\nHost: x\r\n" + headers + b"\r\n\r\n")
        assert b" 400 " in _recv_response(sock)
    assert HttpClient().get(url(server)).status == 200


def test_stop_closes_idle_keep_alive_workers():
    server = HttpServer(port=0)
    server.start()
    try:
        with socket.create_connection(("127.0.0.1", server.port), timeout=2) as sock:
            sock.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
            assert b" 200 " in _recv_response(sock)
            started = time.perf_counter()
            server.stop()
            assert time.perf_counter() - started < 1
            assert sock.recv(1) == b""
            with server._lock:
                assert not server._workers
    finally:
        server.stop()


def test_lowercase_content_type_preserved(server):
    response = HttpClient().post(url(server, "/echo"), b"{}", headers={"content-type": "application/json"})
    assert response.headers["Content-Type"] == "application/json"
