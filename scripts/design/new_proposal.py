"""为一个 Issue 建三套方案的草稿(docs/运营规则.md 7 章)。PM Agent 用。

    python scripts/design/new_proposal.py <编号> [--no-screen]

生成 docs/changes/<编号>/方案/说明.md(功能设计,固定 V1〜V3,V1 是推荐)和 V1.html〜V3.html(画面;--no-screen 时不生成),
docs/changes/<编号>/ 里没有 01-需求.md、02-设计.md 时从 docs/templates/ 复制。已有 说明.md 时不覆盖(退出码 1)。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "design" / "kit"


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="建三套方案的草稿")
    ap.add_argument("issue", type=int)
    ap.add_argument("--no-screen", action="store_true", help="没有画面改动:只写功能设计")
    args = ap.parse_args(argv)
    d = ROOT / "docs" / "changes" / str(args.issue)
    out = d / "方案"
    if (out / "说明.md").exists():
        print(f"new_proposal: {out / '说明.md'} 已经存在,不覆盖(改它,或先和人确认后删掉)", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    made = []
    text = (KIT / "方案说明模板.md").read_text(encoding="utf-8").replace("__编号__", str(args.issue))
    (out / "说明.md").write_text(text, encoding="utf-8")
    made.append(out / "说明.md")
    if not args.no_screen:
        html = (KIT / "画面模板.html").read_text(encoding="utf-8")
        for v, label in (("V1", "V1(推荐)"), ("V2", "V2"), ("V3", "V3")):
            (out / f"{v}.html").write_text(html.replace("__编号__", str(args.issue)).replace("__方案__", label), encoding="utf-8")
            made.append(out / f"{v}.html")
    for name in ("01-需求.md", "02-设计.md"):
        if not (d / name).exists():
            shutil.copyfile(ROOT / "docs" / "templates" / name, d / name)
            made.append(d / name)
    for p in made:
        print(f"  {p.relative_to(ROOT).as_posix()}")
    print(f"new_proposal: #{args.issue} 的草稿 {len(made)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
