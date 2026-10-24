#!/usr/bin/env bash
# 提 PR 前的自查(docs/运营规则.md 4 章)。依次运行,第一个失败就停止,最后输出一段贴进 PR「自查结果」栏的文字。
#
#   bash scripts/dev/precheck.sh [--base <基线>] [--no-fetch] [--skip-tests]
#
#   0. git fetch origin(--no-fetch 不做)
#   1. 有未提交的改动 → NG(测试跑的是工作区,而结果里的 head 指提交)
#   2. 分支名不是 feat/<编号>-<短名> 或 fix/<编号>-<短名> → NG
#   3. 基线前进了 → NG(先 git merge <基线>)
#   4. 与基线的差异里有像密钥的内容 → NG(不显示内容本身)
#   5. project.toml 的 [checks] commands 依次运行
# 结果里像密钥的文字(password=… 等)会被遮住,贴之前仍要看一遍。只检查,不推送、不合并。--skip-tests 时 result=SKIPPED。
set -u
export PYTHONIOENCODING=utf-8

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
top="$(git -C "$here" rev-parse --show-toplevel)"
py="${PYTHON:-python}"
base=""; fetch=1; skip=0
while [ $# -gt 0 ]; do
  case "$1" in
    --base) base="${2:?}"; shift 2 ;;
    --no-fetch) fetch=0; shift ;;
    --skip-tests) skip=1; shift ;;
    *) echo "precheck: 不认识的参数 $1" >&2; exit 2 ;;
  esac
done
if [ $fetch -eq 1 ] && git -C "$top" remote get-url origin >/dev/null 2>&1; then
  git -C "$top" fetch -q origin 2>/dev/null || (cd "$top" && bash scripts/github/bot.sh dev git fetch origin -q) ||
    { echo "precheck: git fetch origin 失败(私有仓库在 Agent 的环境里要经 bot.sh;或加 --no-fetch)" >&2; exit 2; }
fi
if [ -z "$base" ]; then
  if git -C "$top" rev-parse --verify -q origin/main >/dev/null; then base="origin/main"; else base="main"; fi
fi

branch="$(git -C "$top" rev-parse --abbrev-ref HEAD)"
head_sha="$(git -C "$top" rev-parse --short HEAD)"
base_sha="$(git -C "$top" rev-parse --short "$base" 2>/dev/null || echo "?")"
results=()

redact() {
  "$py" -c 'import re,sys; t=sys.stdin.read(); t=re.sub(r"(?i)((password|passwd|pwd|token|secret|api[_-]?key)[=:] *)[^ ,;\"]+", r"\1***", t); sys.stdout.write(re.sub(r"(://[^:/@ ]+:)[^@ ]+@", r"\1***@", t))'
}
finish() {  # $1 = OK / NG / SKIPPED
  echo
  echo "[自查] branch=$branch head=$head_sha base=$base_sha result=$1"
  for r in ${results[@]+"${results[@]}"}; do echo "- $r" | redact; done
  [ "$1" = "OK" ] && exit 0 || exit 1
}
step_ng() { results+=("$1"); finish NG; }

# 1
[ -z "$(git -C "$top" status --porcelain)" ] || step_ng "1 工作区: NG 有未提交的改动,先提交"
results+=("1 工作区: OK")
# 2
[[ "$branch" =~ ^(feat|fix)/[0-9]+-[a-z0-9][a-z0-9-]*$ ]] || step_ng "2 分支名: NG $branch 不是 feat/<编号>-<短名> 或 fix/<编号>-<短名>"
results+=("2 分支名: OK")
# 3
git -C "$top" rev-parse --verify -q "$base^{commit}" >/dev/null || step_ng "3 基线: NG 找不到 $base(写错了?)"
mb="$(git -C "$top" merge-base HEAD "$base" 2>/dev/null || echo "")"
[ "$mb" = "$(git -C "$top" rev-parse "$base" 2>/dev/null)" ] || step_ng "3 基线: NG $base 前进了,先 git merge $base 再自查"
results+=("3 基线: OK 与 $base 同步")
# 4
scan="$(cd "$top" && "$py" scripts/dev/secret_scan.py --base "$base" 2>&1)"; src=$?
[ $src -eq 0 ] || step_ng "4 密钥: NG ${scan#secret_scan: }"
results+=("4 密钥: OK")
# 5
if [ $skip -eq 1 ]; then results+=("5 检查: 跳过(--skip-tests)"); finish SKIPPED; fi
checks=()
while IFS= read -r line; do [ -n "$line" ] && checks+=("$line"); done < <("$py" - "$top/project.toml" <<'PY'
import sys, tomllib
for c in tomllib.load(open(sys.argv[1], "rb")).get("checks", {}).get("commands", []):
    print(c)
PY
)
[ ${#checks[@]} -gt 0 ] || step_ng "5 检查: NG project.toml 的 [checks] commands 是空的"
n=0
for c in "${checks[@]}"; do
  n=$((n + 1))
  echo "== 5.$n $c"
  out="$(cd "$top" && bash -c "$c" 2>&1)"; rc=$?
  printf '%s\n' "$out"
  last="$(printf '%s\n' "$out" | tr -d '\r' | awk 'NF { l = $0 } END { print l }')"
  [ $rc -eq 0 ] || step_ng "5.$n 检查: NG (退出码 $rc) $last"
  results+=("5.$n 检查: OK $last")
done
finish OK
