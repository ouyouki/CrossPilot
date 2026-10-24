"""方案一览(由 scripts/design/open.sh 启动)。git fetch 后,把 origin 上每个 feat|fix 分支的 docs/changes/*/方案/ 取到
tmp/方案一览/<编号>/,生成 index.html(每个 Issue 一行:分支、说明、V1(推荐)〜V3 的画面)并用浏览器打开。
说明.md 转成简单的 HTML(只转义,不解析 Markdown)。不连 git 以外的服务。
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path


def git(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "-c", "core.quotepath=off", *args], capture_output=True, env=env)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    top = git("rev-parse", "--show-toplevel").stdout.decode().strip()
    if not top:
        print("open: 不在 git 仓库里", file=sys.stderr)
        return 2
    os.chdir(top)
    if git("fetch", "-q", "--prune", "origin").returncode != 0:
        print("open: git fetch origin 失败,用本地已有的远端分支", file=sys.stderr)
    out = Path("tmp/方案一览")
    out.mkdir(parents=True, exist_ok=True)
    refs = [r for r in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").stdout.decode("utf-8").split()
            if re.match(r"origin/(feat|fix)/\d+-", r)]
    rows = []
    for ref in sorted(refs, key=lambda r: int(re.search(r"/(\d+)-", r).group(1))):
        n = re.search(r"/(\d+)-", ref).group(1)
        files = [f for f in git("ls-tree", "-r", "--name-only", ref, f"docs/changes/{n}/方案/").stdout.decode("utf-8").splitlines() if f]
        if not files:
            continue
        dest = out / n
        dest.mkdir(exist_ok=True)
        links = []
        for f in files:
            data = git("show", f"{ref}:{f}").stdout
            name = Path(f).name
            if name == "说明.md":
                page = ("<!doctype html><meta charset='utf-8'><title>#" + n + " 说明</title>"
                        "<pre style='white-space:pre-wrap;font:15px/1.6 system-ui,sans-serif;max-width:900px;margin:16px auto;padding:0 16px'>"
                        + html.escape(data.decode("utf-8", "replace")) + "</pre>")
                (dest / "说明.html").write_text(page, encoding="utf-8")
                links.insert(0, f'<a href="{n}/说明.html">说明(功能设计)</a>')
            elif name.endswith(".html"):
                (dest / name).write_bytes(data)
                label = "V1(推荐)" if name == "V1.html" else name[:-5]
                links.append(f'<a href="{n}/{html.escape(name)}">{html.escape(label)}</a>')
        rows.append(f"<tr><td>#{n}</td><td>{html.escape(ref[len('origin/'):])}</td><td>{' · '.join(links)}</td></tr>")
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>方案一览</title>
<style>
:root { --bg:#f7f7f8; --card:#fff; --text:#1d1d1f; --line:#e3e3e6; --a:#2563eb; }
@media (prefers-color-scheme: dark) { :root { --bg:#151517; --card:#1f1f22; --text:#f2f2f4; --line:#2e2e33; --a:#60a5fa; } }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.6 system-ui,"PingFang SC","Microsoft YaHei",sans-serif; }
main { max-width:1000px; margin:0 auto; padding:16px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 16px; overflow-x:auto; }
table { border-collapse:collapse; width:100%; } th,td { text-align:left; padding:8px; border-bottom:1px solid var(--line); }
a { color:var(--a); }
</style></head><body><main>
<h1>方案一览</h1>
<p>定版:在 Issue 上加 <code>设计已批准</code> 并写 <code>[定版] V&lt;编号&gt; &lt;修改意见&gt;</code>;不做的直接关闭 Issue。没空时到时间自动按 V1。</p>
<div class="card"><table><thead><tr><th>Issue</th><th>分支</th><th>方案</th></tr></thead><tbody>
__ROWS__
</tbody></table></div></main></body></html>
""".replace("__ROWS__", "".join(rows) or '<tr><td colspan="3">现在没有方案</td></tr>')
    index = out / "index.html"
    index.write_text(page, encoding="utf-8")
    print(f"open: {len(rows)} 个 Issue 的方案 → {index.as_posix()}")
    if "--no-open" not in sys.argv[1:]:
        webbrowser.open(index.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
