"""在差异里找像密钥的内容(docs/运营规则.md 4、9 章)。自查(precheck.sh)和 CI 都用它。

    python scripts/dev/secret_scan.py --base <基线>      # 检查 git diff <基线>...HEAD 里新增的行
发现时只显示文件名,不显示内容本身。退出码: 0 没有,1 有,2 用法错误。
找的形式: AWS 访问键、私钥的开头、GitHub 令牌、sk- 开头的 API Key,以及 password / secret / api_key / token = "8 个字以上"。
示例文件(*.example、env.example)不查。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

PATTERNS = [
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"ghp_[A-Za-z0-9]{36}",
    r"github_pat_[A-Za-z0-9_]{40,}",
    r"sk-[A-Za-z0-9]{32,}",
    r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
]


def scan(diff: str) -> list[str]:
    hits, current = set(), ""
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r'diff --git "?a/.*?"? "?b/(.*?)"?$', line)
            current = m.group(1) if m else ""
        elif line.startswith("+++ "):
            continue
        elif line.startswith("+") and not line.startswith("+++") and not current.endswith((".example", "env.example")):
            if any(re.search(p, line) for p in PATTERNS):
                hits.add(current)
    return sorted(hits)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="在差异里找像密钥的内容")
    ap.add_argument("--base", required=True)
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    r = subprocess.run(["git", "-c", "core.quotepath=false", "diff", f"{args.base}...HEAD", "--no-color", "--no-ext-diff",
                        "--src-prefix=a/", "--dst-prefix=b/", "-U0"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"secret_scan: git diff 失败: {r.stderr.strip()[:200]}", file=sys.stderr)
        return 2
    hits = scan(r.stdout)
    if hits:
        print(f"secret_scan: 发现像密钥的内容(文件: {' '.join(hits)})。删掉并改用环境变量或设置文件")
        return 1
    print("secret_scan: 没有发现")
    return 0


if __name__ == "__main__":
    sys.exit(main())
