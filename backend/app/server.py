"""标准库适配层:只读接口 + 同意 1 + 审批中心 + 前端静态文件。

    python -m app.server        # http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from crosspilot.core.errors import ToolGateError

from . import approvals_api, handlers, selection

ROUTES = {
    "/healthz": handlers.health,
    "/api/v1/today": handlers.today,
    "/api/v1/candidates": handlers.candidates,
    "/api/v1/approvals": selection.approvals,
}

_APPROVAL_GET = re.compile(r"^/api/v1/approvals/([\w-]+)$")
_APPROVAL_VIEWS = re.compile(r"^/api/v1/approvals/([\w-]+)/views$")
_APPROVAL_DECIDE = re.compile(r"^/api/v1/approvals/([\w-]+)/decide$")
_SELECTION = "/api/v1/approvals/selection"

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        route = ROUTES.get(path.rstrip("/") or "/")
        if route is not None:
            self._json(200, route())
            return
        match = _APPROVAL_GET.match(path)
        if match:
            self._call(lambda: approvals_api.detail(match.group(1)))
            return
        if path.startswith("/api/") or path == "/healthz":
            self._problem(404, "NOT_FOUND", path)
            return
        self._static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/")
        try:
            body = self._body()
        except ValueError as error:
            self._problem(400, "BAD_JSON", str(error))
            return

        if path == _SELECTION:
            try:
                result = selection.create_selection(body.get("subject_refs") or [])
            except selection.SelectionError as error:
                self._problem(422, error.code, error.detail)
                return
            self._json(201 if not result.get("duplicate") else 200, result)
            return

        match = _APPROVAL_VIEWS.match(path)
        if match:
            self._call(lambda: approvals_api.record_view(match.group(1), str(body.get("section", ""))))
            return

        match = _APPROVAL_DECIDE.match(path)
        if match:
            self._call(lambda: approvals_api.decide(match.group(1), body))
            return

        self._problem(404, "NOT_FOUND", path)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("请求体要是 JSON 对象")
        return parsed

    def _call(self, fn) -> None:
        try:
            self._json(200, fn())
        except approvals_api.ApprovalNotFound as error:
            self._problem(404, "NOT_FOUND", str(error))
        except ToolGateError as error:
            self._problem(error.http_status, error.code, error.detail)
        except ValueError as error:
            self._problem(400, "BAD_REQUEST", str(error))

    def _static(self, path: str) -> None:
        if not DIST.is_dir():
            self._problem(503, "FRONTEND_NOT_BUILT", "先运行 cd frontend && npm install && npm run build")
            return
        target = (DIST / path.lstrip("/")).resolve()
        if not str(target).startswith(str(DIST.resolve())) or not target.is_file():
            target = DIST / "index.html"
        if not target.is_file():
            self._problem(404, "NOT_FOUND", path)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _TYPES.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code: int, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _problem(self, code: int, title: str, detail: str) -> None:
        self._json(code, {"type": "about:blank", "title": title, "status": code, "code": title, "detail": detail})

    def log_message(self, *args: object) -> None:
        return


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:  # pragma: no cover
    server = make_server()
    host, port = server.server_address[0], server.server_address[1]
    print(f"CrossPilot: http://{host}:{port}  (Ctrl+C 结束)")
    server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
