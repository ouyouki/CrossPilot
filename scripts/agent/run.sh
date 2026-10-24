#!/usr/bin/env bash
# 一个环境的循环:问调度下一步做什么,用 harness 的无界面模式启动对应的 Agent,做完再问(docs/运营规则.md 5 章)。
#
#   bash scripts/agent/run.sh <dev|pm|review> [--until HH:MM] [--once] [--dry-run] [--state <JSON>]
#
# 说明和上限(每天的次数、Token 的预算、重试)见 scripts/agent/run.py 的开头和 project.toml 的 [runner]。
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for py in python3 python "py -3"; do
  if $py -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
    exec $py "$here/run.py" "$@"
  fi
done
echo "run.sh: 找不到 Python 3.11 以上" >&2
exit 2
