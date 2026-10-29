import pytest

from src.http.request import Request
from src.http.response import Response
from src.http.serializer import Serializer
from src.http.url import ParseError

s = Serializer()


def test_request_ends_header_separator():
    raw = s.serialize_request(Request("GET", "/", headers={"Host": "x"}))
    assert raw.endswith(b"\r\n\r\n")


def test_response_content_length():
    raw = s.serialize_response(Response(200, body=b"abc"))
    assert b"Content-Length: 3\r\n" in raw


def test_request_body_content_length():
    raw = s.serialize_request(Request("POST", "/", headers={"Host": "x"}, body=b"abc"))
    assert b"Content-Length: 3\r\n" in raw


def test_response_has_date():
    assert b"Date:" in s.serialize_response(Response(204))


def test_custom_reason_is_preserved():
    raw = s.serialize_response(Response(299, reason="Custom"))
    assert raw.startswith(b"HTTP/1.1 299 Custom\r\n")


def test_response_has_default_content_type():
    raw = s.serialize_response(Response(204))
    assert b"Content-Type: application/octet-stream\r\n" in raw


def test_empty_post_has_content_length():
    assert b"Content-Length: 0\r\n" in s.serialize_request(Request("POST", "/echo", headers={"Host": "x"}))


def test_response_defaults_are_case_insensitive():
    raw = s.serialize_response(Response(200, headers={"content-type": "text/plain", "content-length": "3"}, body=b"abc"))
    assert raw.lower().count(b"content-type:") == 1
    assert raw.lower().count(b"content-length:") == 1


def test_reject_header_injection():
    with pytest.raises(ParseError):
        s.serialize_request(Request("GET", "/", headers={"Host": "x", "X-Test": "value\r\nInjected: yes"}))


def test_reject_mismatched_content_length():
    with pytest.raises(ParseError):
        s.serialize_request(Request("POST", "/echo", headers={"Host": "x", "Content-Length": "1"}, body=b"abc"))
