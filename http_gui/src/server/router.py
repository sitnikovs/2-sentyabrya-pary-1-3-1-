from typing import Callable, Dict, Tuple
from ..http.request import Request
from ..http.response import Response

Handler = Callable[[Request], Response]


class Router:
    def __init__(self):
        self._routes: Dict[Tuple[str, str], Handler] = {}

    def route(self, method: str, path: str, handler: Handler):
        self._routes[(method.upper(), path)] = handler

    def dispatch(self, req: Request) -> Response:
        handler = self._routes.get((req.method.upper(), req.path.split("?", 1)[0]))
        if handler:
            return handler(req)
        path = req.path.split("?", 1)[0]
        if req.method.upper() == "GET" and path.startswith("/status/"):
            try:
                code = int(path.rsplit("/", 1)[1])
                if 100 <= code <= 599:
                    return Response(code, body=b"")
            except ValueError:
                pass
        return Response(404, "Not Found", headers={"Content-Type": "text/plain; charset=utf-8"}, body=b"404 Not Found")
