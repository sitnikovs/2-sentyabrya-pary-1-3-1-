import pytest
from src.http.parser import Parser
from src.http.url import ParseError

p = Parser()


def test_parse_get():
    r = p.parse_request(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
    assert r.method == "GET" and r.path == "/"


def test_request_body():
    r = p.parse_request(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 3\r\n\r\nabc")
    assert r.body == b"abc"


def test_missing_host():
    with pytest.raises(ParseError):
        p.parse_request(b"GET / HTTP/1.1\r\n\r\n")


def test_bad_request_line():
    with pytest.raises(ParseError):
        p.parse_request(b"GARBAGE\r\nHost: x\r\n\r\n")


def test_header_overflow():
    with pytest.raises(ParseError):
        p.parse_request(b"GET / HTTP/1.1\r\nX: " + b"a" * 9000 + b"\r\n\r\n")


def test_parse_response():
    r = p.parse_response(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
    assert r.status == 200 and r.body == b"OK"


def test_chunked_response():
    r = p.parse_response(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n")
    assert r.body == b"Wikipedia"


def test_invalid_content_length():
    with pytest.raises(ParseError):
        p.parse_response(b"HTTP/1.1 200 OK\r\nContent-Length: nope\r\n\r\n")


def test_http_10_does_not_require_host():
    request = p.parse_request(b"GET / HTTP/1.0\r\n\r\n")
    assert request.version == "HTTP/1.0"


def test_incomplete_request_body():
    with pytest.raises(ParseError):
        p.parse_request(
            b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\n\r\nabc"
        )


def test_negative_content_length():
    with pytest.raises(ParseError):
        p.parse_request(
            b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: -1\r\n\r\n"
        )


@pytest.mark.parametrize("headers", [
    b"Host: x\r\nHost: y",
    b"Host: x\r\nContent-Length: 0\r\ncontent-length: 3",
    b"Host: x\r\nContent-Length: 0\r\nTransfer-Encoding: chunked",
    b"Host: x\r\nContent-Length: ",
    b"Host: x\r\nContent-Length: +1",
    b"Host : x",
    b"Host: x\r\nBad Name: value",
    b"Host: x\r\nX-Test: a\x00b",
])
def test_reject_ambiguous_or_malformed_headers(headers):
    with pytest.raises(ParseError):
        p.parse_request(b"GET / HTTP/1.1\r\n" + headers + b"\r\n\r\n")


@pytest.mark.parametrize("body", [b"0\r\n", b"-1\r\nx\r\n0\r\n\r\n", b"1\r\nx!\r\n0\r\n\r\n"])
def test_reject_incomplete_or_invalid_chunked_body(body):
    with pytest.raises(ParseError):
        p.decode_chunked(body)


def test_chunk_extensions_and_trailers():
    assert p.decode_chunked(b"3;ext=yes\r\nabc\r\n0;end=yes\r\nX-Check: ok\r\n\r\n") == b"abc"


def test_response_rejects_conflicting_framing():
    with pytest.raises(ParseError):
        p.parse_response(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n")


def test_response_304_does_not_have_a_body():
    response = p.parse_response(b"HTTP/1.1 304 Not Modified\r\nContent-Length: 500\r\n\r\n")
    assert response.status == 304 and response.body == b""


def test_invalid_http_version():
    with pytest.raises(ParseError):
        p.parse_request(b"GET / HTTP/nope\r\nHost: x\r\n\r\n")
