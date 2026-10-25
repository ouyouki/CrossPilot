#!/usr/bin/env bash
# 为一个 Issue 创建工作树和分支(docs/运营规则.md 4 章)。
#
#   bash scripts/dev/new_issue.sh <Issue 编号> <英文短名> [--fix] [--dir <文件夹>] [--dry-run]
#
#   1. git fetch origin(没有凭据时经 bot.sh,用这个环境的 App 身份 BOT_ROLE)
#   2. 远端已有这个 Issue 的分支(PM Agent 建的)→ 从它建工作树;没有 → 从 origin/main 建 feat/<编号>-<短名>(--fix 时 fix/…)
#      (--no-track:不让新分支的 upstream 指向 main,避免误推)
# 默认文件夹: <本仓库>/.worktrees/<编号>(建在仓库里,沙箱才覆盖得到;要放别处用 --dir)。--dry-run 只检查参数并列出步骤。不推送。
set -eu
export PYTHONIOENCODING=utf-8

usage() { echo "用法: bash scripts/dev/new_issue.sh <编号> <英文短名> [--fix] [--dir <文件夹>] [--dry-run]" >&2; exit 2; }
[ $# -lt 2 ] && usage
num="$1"; slug="$2"; shift 2
kind="feat"; dir=""; dry=0
while [ $# -gt 0 ]; do
  case "$1" in
    --fix) kind="fix"; shift ;;
    --dir) dir="${2:?}"; shift 2 ;;
    --dry-run) dry=1; shift ;;
    *) usage ;;
  esac
done
[[ "$num" =~ ^[0-9]+$ ]] || { echo "new_issue: Issue 编号要是数字($num)" >&2; exit 2; }
[[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "new_issue: 短名只用英文小写、数字、连字符($slug)" >&2; exit 2; }

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
top="$(git -C "$here" rev-parse --show-toplevel)"
branch="$kind/$num-$slug"
[ -z "$dir" ] && dir="$top/.worktrees/$num"
case "$dir" in /*|[A-Za-z]:*) ;; *) dir="$(pwd)/$dir" ;; esac

echo "new_issue: #$num → $branch"
echo "  1. git fetch origin"
echo "  2. git worktree add --no-track -b $branch $dir origin/main"
if [ $dry -eq 1 ]; then echo "new_issue: --dry-run,什么都没做"; exit 0; fi

[ -e "$dir" ] && { echo "new_issue: $dir 已经存在" >&2; exit 1; }
GIT_TERMINAL_PROMPT=0 git -C "$top" fetch -q origin 2>/dev/null || (cd "$top" && bash scripts/github/bot.sh "${BOT_ROLE:-dev}" git fetch origin -q) ||
  { echo "new_issue: git fetch 失败(私有仓库在 Agent 的环境里要经 bot.sh)" >&2; exit 1; }
existing=""
[ "$slug" = revert ] || existing="$(git -C "$top" for-each-ref --format='%(refname:short)' "refs/remotes/origin/feat/$num-*" "refs/remotes/origin/fix/$num-*" \
  | grep -v -- '-revert$' | head -n 1)"
if [ -n "$existing" ]; then
  branch="${existing#origin/}"
  echo "new_issue: 远端已有 $branch,从它建工作树"
  git -C "$top" worktree add -q --no-track -b "$branch" "$dir" "$existing"
else
  git -C "$top" worktree add -q --no-track -b "$branch" "$dir" origin/main
fi
echo "new_issue: 好了: $dir($branch)。在那里启动 Agent。"
