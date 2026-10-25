"""标准库适配层(02-设计 §1):只读接口 + 同意 1 的提交 + 前端静态文件。

    python -m app.server        # http://127.0.0.1:8000
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import handlers, selection

ROUTES = {
    "/healthz": handlers.health,
    "/api/v1/today": handlers.today,
    "/api/v1/candidates": handlers.candidates,
    "/api/v1/approvals": selection.approvals,
}

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
    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        path = self.path.split("?", 1)[0]
        route = ROUTES.get(path.rstrip("/") or "/")
        if route is not None:
            self._json(200, route())
            return
        if path.startswith("/api/") or path == "/healthz":
            self._problem(404, "NOT_FOUND", path)
            return
        self._static(path)

    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        path = self.path.split("?", 1)[0].rstrip("/")
        if path != "/api/v1/approvals/selection":
            self._problem(404, "NOT_FOUND", path)
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise selection.SelectionError("BAD_BODY", "请求体要是 JSON 对象")
            result = selection.create_selection(body.get("subject_refs") or [])
        except selection.SelectionError as error:
            self._problem(422, error.code, error.detail)
            return
        except (json.JSONDecodeError, ValueError) as error:
            self._problem(400, "BAD_JSON", str(error))
            return
        self._json(201 if not result.get("duplicate") else 200, result)

    def _static(self, path: str) -> None:
        if not DIST.is_dir():
            self._problem(503, "FRONTEND_NOT_BUILT", "先运行 cd frontend && npm install && npm run build")
            return
        target = (DIST / path.lstrip("/")).resolve()
        if not str(target).startswith(str(DIST.resolve())) or not target.is_file():
            target = DIST / "index.html"  # SPA 回退
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
        self._json(
            code,
            {"type": "about:blank", "title": title, "status": code, "code": title, "detail": detail},
        )

    def log_message(self, *args: object) -> None:  # 不打印访问日志
        return


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:  # pragma: no cover - 手动启动
    server = make_server()
    host, port = server.server_address[0], server.server_address[1]
    print(f"CrossPilot: http://{host}:{port}  (Ctrl+C 结束)")
    server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
