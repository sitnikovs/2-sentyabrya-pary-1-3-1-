from abc import ABC, abstractmethod
from .request import Request
from .response import Response


class HttpParser(ABC):
    @abstractmethod
    def parse_request(self, data: bytes) -> Request:
        raise NotImplementedError

    @abstractmethod
    def parse_response(self, data: bytes) -> Response:
        raise NotImplementedError


class HttpSerializer(ABC):
    @abstractmethod
    def serialize_request(self, request: Request) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def serialize_response(self, response: Response) -> bytes:
        raise NotImplementedError
