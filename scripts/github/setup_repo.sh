#!/usr/bin/env bash
# 仓库的初始设置(docs/运营规则.md 2、4 章)。由人用自己的 gh 登录运行一次(Agent 不运行:命令监视会拦下)。
#
#   bash scripts/github/setup_repo.sh [--dry-run]
#
#   1. 按 .github/labels.json 创建或更新标签
#   2. 按 .github/rulesets/*.json 创建规则集(已有同名的就跳过)
#   3. 打开依赖的漏洞提醒(Dependabot alerts;依赖的版本更新由 .github/dependabot.yml 提 PR)
#   4. 列出要在网页上做的事(GitHub App、Environment、合并方式)
# 规则集在私有仓库需要对应的 GitHub 套餐;不支持时会报错,见 引导手册。--dry-run 只列出要做的事。
set -u
export PYTHONIOENCODING=utf-8
top="$(git rev-parse --show-toplevel)"; cd "$top"
py="${PYTHON:-python}"
dry=0; [ "${1:-}" = "--dry-run" ] && dry=1
repo="$("$py" -c 'import tomllib; d=tomllib.load(open("project.toml","rb"))["github"]; print(d["owner"]+"/"+d["repo"])')"
case "$repo" in *"{{"*) echo "setup_repo: 先填 project.toml 的 [github]" >&2; exit 2 ;; esac
run() { if [ $dry -eq 1 ]; then echo "  (dry-run) $*"; else "$@"; fi; }

echo "== 1 标签"
"$py" -c 'import json; [print(l["name"]+"\t"+l["color"]+"\t"+l["description"]) for l in json.load(open(".github/labels.json", encoding="utf-8"))]' |
while IFS=$'\t' read -r name color desc; do
  run gh label create "$name" --repo "$repo" --color "$color" --description "$desc" --force >/dev/null
  echo "  $name"
done

echo "== 2 规则集"
existing="$(gh api "repos/$repo/rulesets" --jq '.[].name' 2>/dev/null || true)"
for f in .github/rulesets/*.json; do
  name="$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["name"])' "$f")"
  if printf '%s\n' "$existing" | grep -qxF "$name"; then echo "  已有: $name"; continue; fi
  run gh api -X POST "repos/$repo/rulesets" --input "$f" >/dev/null && echo "  已创建: $name"
done

echo "== 3 依赖的漏洞提醒"
run gh api -X PUT "repos/$repo/vulnerability-alerts" >/dev/null && echo "  已打开"

cat <<'TXT'
== 4 在网页上做(见 引导手册)
  - 建三个 GitHub App(开发用、PM 用、评审用),只给这个仓库装上;权限: Contents 读写、Issues 读写、Pull requests 读写、Metadata 读
    (不给 Actions、Workflows、Administration、Commit statuses);三个私钥分别只放在开发、PM、评审环境里
  - 合并方式只留 squash;打开 "Automatically delete head branches"
  - Settings › Environments › production:若套餐支持,设 Required reviewers(你)并勾选 Prevent self-review
  - Settings › Actions › General:Workflow permissions 选 "Read repository contents"(各工作流自己声明需要的写权限)
  - 公开仓库可以再打开 Settings › Code security › Secret scanning 和 CodeQL(免费;私有仓库要 GitHub 的付费功能)
TXT
