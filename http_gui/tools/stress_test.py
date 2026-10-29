"""Run 100 parallel GET requests against an ephemeral local HttpServer."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.client.http_client import HttpClient
from src.server.http_server import HttpServer


def main():
    server = HttpServer(port=0)
    server.start()
    target = f"http://127.0.0.1:{server.port}/"

    def request(_):
        return HttpClient(timeout_ms=3000).get(target).status

    try:
        with ThreadPoolExecutor(max_workers=20) as pool:
            statuses = list(pool.map(request, range(100)))
        print(f"requests={len(statuses)}")
        print(f"status_200={statuses.count(200)}")
        print(f"all_ok={all(status == 200 for status in statuses)}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
