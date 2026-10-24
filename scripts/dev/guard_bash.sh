#!/usr/bin/env bash
# 用找到的第一个 Python(python3、python、py -3)启动 guard_bash.py。一个都找不到时拦下命令(退出码 2):
# 监视自己起不来时不能放行所有命令。Claude Code 的 PreToolUse hook 和 OpenCode 的插件都调用这里(docs/运营规则.md 9 章)。
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
input="$(cat)"
for py in python3 python "py -3"; do
  if $py -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    printf '%s' "$input" | $py "$here/guard_bash.py"
    exit $?
  fi
done
echo "guard_bash: 找不到 Python,已拦下命令。请安装 Python 3(见 引导手册)。" >&2
exit 2
