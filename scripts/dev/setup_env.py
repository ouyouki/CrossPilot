"""从 docker/env.example 生成本机的开发环境设置文件(docs/运营规则.md 11 章)。

    python scripts/dev/setup_env.py [--example docker/env.example] [--out docker/.env] [--set KEY=VALUE ...]

* 逐行复制示例;值写成 <random> 的项目,换成在本机新生成的随机值(secrets.token_urlsafe)。
* 不显示任何值(只显示填了哪些项目名),不覆盖已有的文件(要重做就自己先删),拒绝写进会被 git 跟踪的文件
  (必须在 .gitignore 里),这样密钥不会进 git、聊天或评论。
* 一次性环境不用另一个设置文件: docker compose -p <名字> 加上 shell 的 APP_PORT=<端口>(shell 的变量优先)。
退出码: 0 已生成或已存在,2 用法错误或被拒绝。
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="生成本机的开发环境设置文件(随机密钥)")
    ap.add_argument("--example", default="docker/env.example")
    ap.add_argument("--out", default="docker/.env")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    example, out = Path(args.example), Path(args.out)
    if not example.is_file():
        print(f"setup_env: 找不到 {example}", file=sys.stderr)
        return 2
    if out.exists():
        print(f"setup_env: {out} 已经存在(不覆盖。要重做就自己先删掉)")
        return 0
    ignored = subprocess.run(["git", "check-ignore", "-q", str(out)], capture_output=True).returncode == 0
    if not ignored:
        print(f"setup_env: {out} 不在 .gitignore 里。为了不让密钥进 git,不写", file=sys.stderr)
        return 2
    example_lines = example.read_text(encoding="utf-8").splitlines()
    filled: list[str] = []
    lines = []
    for line in example_lines:
        m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line)
        if m and m.group(2).strip() == "<random>":
            line = f"{m.group(1)}={secrets.token_urlsafe(24)}"
            filled.append(m.group(1))
        lines.append(line)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:   # created exclusively, readable by this user only (on Windows the mode is ignored)
        fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        print(f"setup_env: {out} 已经存在(不覆盖)")
        return 0
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"setup_env: 已生成 {out}(随机生成的项目: {', '.join(filled) or '无'}。不显示值)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
