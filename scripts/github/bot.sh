#!/usr/bin/env bash
# 以 GitHub App 的身份运行一条 gh 或 git 命令(docs/运营规则.md 2、9 章)。
#
# 允许清单、拒绝规则、设置怎么读,全在 scripts/github/bot.py 里(2026-10-25 从本文件搬过去)。
# 搬的理由:bash 在沙箱里起不来(NtCreateDirectoryObject(\BaseNamedObjects\msys-2.0...) 0xC0000022)、
# openssl 常常不在 PATH、gh 未必装 —— 这三样正是这一层最不该依赖的东西。
# 留两份清单会漂,所以这里只负责找到 Python,把参数原样交过去。
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for py in python3 python "py -3"; do
  if $py -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
    exec $py "$here/bot.py" "$@"
  fi
done
echo "bot.sh: 找不到 Python 3.11 以上(tomllib 读 project.toml 要用)。" >&2
exit 2
