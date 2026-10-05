"""Serve the EP prototype and its read-only, server-side GHL account adapter."""
import argparse
import copy
import json
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from check_ghl_accounts import AccountCheckError, fetch_accounts
from check_ghl_statistics import fetch_statistics

DIST = Path(__file__).resolve().parents[1] / "dist"
EXPECTED_PLATFORMS = ("instagram", "linkedin", "tiktok", "youtube", "facebook")


class AccountsStore:
    def __init__(self, loader=fetch_accounts, ttl_seconds=60, clock=time.monotonic):
        self.loader = loader
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self.lock = threading.Lock()
        self.snapshot = None
        self.fetched_at = None

    def decorate(self, result):
        result["source"] = "gohighlevel"
        result["checkedAt"] = datetime.now(timezone.utc).isoformat()
        platforms = {account.get("platform") for account in result["accounts"]}
        result["missingPlatforms"] = [name for name in EXPECTED_PLATFORMS if name not in platforms]
        result["capabilities"] = {"accountRead": "verified", "analytics": "not_verified", "publishing": "not_verified"}
        return result

    def get_snapshot(self):
        with self.lock:
            cached = self.snapshot is not None and self.clock() - self.fetched_at < self.ttl_seconds
            if not cached:
                # A failure does not refresh the age or serve old data as newly checked.
                result = self.loader()
                self.snapshot = self.decorate(copy.deepcopy(result))
                self.fetched_at = self.clock()
            response = copy.deepcopy(self.snapshot)
            response["cache"] = {"fromCache": cached, "ttlSeconds": self.ttl_seconds}
            return response


class StatisticsStore(AccountsStore):
    def __init__(self, loader=fetch_statistics, ttl_seconds=60, clock=time.monotonic):
        super().__init__(loader=loader, ttl_seconds=ttl_seconds, clock=clock)

    def decorate(self, result):
        result["source"] = "gohighlevel"
        result["checkedAt"] = datetime.now(timezone.utc).isoformat()
        return result


def create_server(port=8000, store=None, dist_dir=None, statistics_store=None):
    account_store = store if store is not None else AccountsStore()
    stats_store = statistics_store if statistics_store is not None else StatisticsStore(
        loader=lambda: fetch_statistics(account_loader=lambda _location, _token: account_store.get_snapshot())
    )
    root = Path(dist_dir if dist_dir is not None else DIST).resolve()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *_args):
            # Avoid logging arbitrary URLs, headers or upstream exception data.
            pass

        def send_json(self, code, data, head=False):
            payload = json.dumps(data, ensure_ascii=True).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if not head:
                self.wfile.write(payload)

        def allowed_request(self):
            port = self.server.server_port
            hosts = self.headers.get_all("Host", [])
            if len(hosts) != 1 or hosts[0].lower() not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                self.send_json(403, {"error": {"code": "HOST_DENIED", "message": "This local workspace address is not allowed."}})
                return False
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{hosts[0].lower()}":
                self.send_json(403, {"error": {"code": "ORIGIN_DENIED", "message": "Open this request from the local workspace."}})
                return False
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                self.send_json(403, {"error": {"code": "ORIGIN_DENIED", "message": "Open this request from the local workspace."}})
                return False
            target = urlsplit(self.path)
            if target.scheme or target.netloc:
                self.send_json(400, {"error": {"code": "REQUEST_INVALID", "message": "Use a local workspace path."}})
                return False
            return True

        def safe_static(self):
            candidate = Path(self.translate_path(self.path)).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                self.send_json(403, {"error": {"code": "PATH_DENIED", "message": "This file is outside the workspace assets."}})
                return False
            # A symlinked directory must not expose an outside listing either.
            if candidate.is_dir() and any(p.is_symlink() and not p.resolve().is_relative_to(root) for p in candidate.iterdir()):
                self.send_json(403, {"error": {"code": "PATH_DENIED", "message": "This file is outside the workspace assets."}})
                return False
            return True

        def do_GET(self):
            if not self.allowed_request():
                return
            path = urlsplit(self.path).path
            if path == "/api/health":
                self.send_json(200, {"status": "ok"})
            elif path in ("/api/social/accounts", "/api/social/statistics"):
                try:
                    selected_store = account_store if path == "/api/social/accounts" else stats_store
                    self.send_json(200, selected_store.get_snapshot())
                except AccountCheckError as error:
                    diagnostic = {"code": error.code, "message": error.message}
                    if error.upstream_status is not None:
                        diagnostic["upstreamStatus"] = error.upstream_status
                    if error.proxy_status is not None:
                        diagnostic["proxyStatus"] = error.proxy_status
                    self.send_json(error.http_status, {"error": diagnostic})
                except Exception:
                    self.send_json(502, {"error": {"code": "SOCIAL_LOOKUP_FAILED", "message": "Social data could not be loaded. Try again shortly."}})
            elif path.startswith("/api/"):
                self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "This workspace endpoint does not exist."}})
            elif self.safe_static():
                super().do_GET()

        def do_HEAD(self):
            if not self.allowed_request():
                return
            if urlsplit(self.path).path.startswith("/api/"):
                self.send_json(405, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET for this read-only endpoint."}}, head=True)
            elif self.safe_static():
                super().do_HEAD()

        def do_POST(self):
            self.close_connection = True
            if self.allowed_request():
                self.send_json(405, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "This workspace endpoint is read-only."}})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST
        do_OPTIONS = do_POST

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = create_server(port=args.port)
    print(f"EP development server started on local port {server.server_port}.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
