"""令牌代理(docs/运营规则.md 9.1;引导手册 4 步的「私钥不给 Agent」)。

App 的私钥只放在运行这个代理的系统用户那里;Agent 的环境只有一个"取令牌的口令",向代理要 1 小时有效、只限本仓库的安装令牌。
这样 Agent 被网页或文档里的"指示"带偏时,也拿不走私钥;口令泄露时,只要在代理这边换掉口令。

    python scripts/github/token_broker.py --repo <所有者>/<仓库> [--config-dir <目录>] [--port 8787] [--dry-run]
    python scripts/github/token_broker.py --hash < 口令文件        # 显示口令的 sha256(写进代理的设置)

设置(代理的系统用户才能读;不进 git): <目录>/<dev|pm|review>.env(默认目录 ~/.github-bots/broker)
    APP_ID=<App 的 ID>  INSTALLATION_ID=<安装 ID>  PRIVATE_KEY_FILE=<私钥 .pem>  CLIENT_SECRET_SHA256=<口令的 sha256>
只监听 127.0.0.1。请求: GET /token/<dev|pm|review>,头 Authorization: Bearer <口令>;口令要和那个身份的一致。
权限和 bot.sh 原来的一样(评审只读代码)。令牌在过期前 10 分钟内重新取;令牌和 JWT 不写进日志和文件。
--dry-run:只签 JWT,不连 GitHub,发一个假的令牌(测试用)。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROLES = ("dev", "pm", "review")
PERMS = {"review": {"contents": "read", "issues": "write", "pull_requests": "write", "metadata": "read"}}
DEFAULT_PERMS = {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_env(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k.strip()] = v.strip().strip('"')
    if not (out.get("APP_ID", "").isdigit() and out.get("INSTALLATION_ID", "").isdigit()
            and Path(out.get("PRIVATE_KEY_FILE", "")).is_file() and re.fullmatch(r"[0-9a-f]{64}", out.get("CLIENT_SECRET_SHA256", ""))):
        raise SystemExit(f"token_broker: {path} 要有数字的 APP_ID、INSTALLATION_ID,存在的 PRIVATE_KEY_FILE,64 位的 CLIENT_SECRET_SHA256")
    return out


def jwt(app_id: str, key_file: str) -> str:
    now = int(time.time())
    head = b64url(b'{"alg":"RS256","typ":"JWT"}')
    claims = b64url(json.dumps({"iat": now - 60, "exp": now + 540, "iss": app_id}).encode())
    r = subprocess.run(["openssl", "dgst", "-sha256", "-sign", key_file, "-binary"], input=f"{head}.{claims}".encode(), capture_output=True)
    if r.returncode or not r.stdout:
        raise RuntimeError("用私钥签名失败")
    return f"{head}.{claims}.{b64url(r.stdout)}"


class Broker:
    def __init__(self, repo: str, conf: dict[str, dict[str, str]], dry: bool):
        self.owner, self.repo = repo.split("/", 1)
        self.conf, self.dry = conf, dry
        self.cache: dict[str, tuple[str, float]] = {}
        self.lock = threading.Lock()

    def allowed(self, role: str, secret: str) -> bool:
        c = self.conf.get(role)
        return bool(c) and hmac.compare_digest(hashlib.sha256(secret.encode()).hexdigest(), c["CLIENT_SECRET_SHA256"])

    def token(self, role: str) -> tuple[str, float]:
        with self.lock:
            tok, exp = self.cache.get(role, ("", 0))
            if tok and exp - time.time() > 600:
                return tok, exp
            c = self.conf[role]
            signed = jwt(c["APP_ID"], c["PRIVATE_KEY_FILE"])
            if self.dry:
                tok, exp = f"dryrun-{role}-{int(time.time())}", time.time() + 3600
            else:
                body = json.dumps({"repositories": [self.repo], "permissions": PERMS.get(role, DEFAULT_PERMS)}).encode()
                req = urllib.request.Request(f"https://api.github.com/app/installations/{c['INSTALLATION_ID']}/access_tokens", data=body,
                                             method="POST", headers={"Authorization": f"Bearer {signed}",
                                                                     "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    d = json.load(r)
                tok = d["token"]
                exp = datetime.fromisoformat(d["expires_at"].replace("Z", "+00:00")).timestamp()
            self.cache[role] = (tok, exp)
            return tok, exp


def serve(broker: Broker, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):                       # no request lines (they carry nothing secret, but keep logs small)
            pass

        def reply(self, code: int, obj: dict) -> None:
            data = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            m = re.fullmatch(r"/token/(dev|pm|review)", self.path)
            auth = self.headers.get("Authorization", "")
            if not m:
                return self.reply(404, {"message": "只有 /token/<dev|pm|review>"})
            role = m.group(1)
            if not auth.startswith("Bearer ") or not broker.allowed(role, auth[7:]):
                print(f"token_broker: {datetime.now():%H:%M:%S} 拒绝 {role}(口令不对)", file=sys.stderr, flush=True)
                return self.reply(403, {"message": "口令不对"})
            try:
                tok, exp = broker.token(role)
            except (RuntimeError, OSError, urllib.error.URLError, KeyError, ValueError) as e:
                print(f"token_broker: {datetime.now():%H:%M:%S} {role} 取令牌失败: {type(e).__name__}", file=sys.stderr, flush=True)
                return self.reply(502, {"message": f"取不到安装令牌({type(e).__name__});看代理的输出"})
            print(f"token_broker: {datetime.now():%H:%M:%S} 发给 {role}", file=sys.stderr, flush=True)
            self.reply(200, {"token": tok, "expires_at": int(exp)})

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"token_broker: 在 127.0.0.1:{port} 等待(身份 {', '.join(broker.conf)}{',dry-run' if broker.dry else ''})", file=sys.stderr, flush=True)
    srv.serve_forever()


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="GitHub App 的令牌代理")
    ap.add_argument("--repo")
    ap.add_argument("--config-dir", default=os.path.expanduser("~/.github-bots/broker"))
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hash", action="store_true")
    args = ap.parse_args(argv)
    if args.hash:
        print(hashlib.sha256("".join(sys.stdin.read().split()).encode()).hexdigest())   # 和 bot.sh 一样去掉所有空白
        return 0
    if not args.repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        print("token_broker: 要 --repo <所有者>/<仓库>", file=sys.stderr)
        return 2
    d = Path(args.config_dir)
    conf = {r: load_env(d / f"{r}.env") for r in ROLES if (d / f"{r}.env").is_file()}
    if not conf:
        print(f"token_broker: {d} 里没有 dev.env / pm.env / review.env", file=sys.stderr)
        return 2
    serve(Broker(args.repo, conf, args.dry_run), args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
