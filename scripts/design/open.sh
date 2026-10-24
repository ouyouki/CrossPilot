#!/usr/bin/env bash
# 方案一览(人用,在自己的环境里运行;docs/运营规则.md 7 章):取下远端所有 feat|fix 分支上的方案,生成 tmp/方案一览/index.html 并打开。
#
#   bash scripts/design/open.sh [--no-open]
#
# 只读 git(git fetch),不连别的服务,不发布到外部。--no-open 只生成不打开。
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for py in python3 python "py -3"; do
  if $py -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    exec $py "$here/open_index.py" "$@"
  fi
done
echo "open.sh: 找不到 Python 3" >&2
exit 2
