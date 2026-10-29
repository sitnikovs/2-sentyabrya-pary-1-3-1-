import pytest
from src.http.url import ParseError, Url


def test_url_full():
    u = Url.parse("http://host:8080/path?q=1")
    assert (u.host, u.port, u.path, u.query) == ("host", 8080, "/path", "q=1")


def test_url_default_port():
    assert Url.parse("http://host/path").port == 80


def test_https_default_port():
    assert Url.parse("https://host/").port == 443


def test_invalid_url():
    with pytest.raises(ParseError):
        Url.parse("garbage")


def test_query_target():
    assert Url.parse("http://x/a?b=1").target == "/a?b=1"


def test_url_root_path_when_omitted():
    assert Url.parse("http://example.com").path == "/"


def test_invalid_port_range():
    with pytest.raises(ParseError):
        Url.parse("http://host:70000/")


@pytest.mark.parametrize("value", ["http://host:0/", "http://host/a b", "http://host/\r\nX-Test: value"])
def test_invalid_port_or_control_characters(value):
    with pytest.raises(ParseError):
        Url.parse(value)


def test_ipv6_host_header():
    assert Url.parse("http://[::1]:8080/").host_header == "[::1]:8080"
