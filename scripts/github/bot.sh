#!/usr/bin/env bash
# 以 GitHub App 的身份运行一条 gh 或 git 命令(docs/运营规则.md 0、9 章)。Agent 对 GitHub 的所有操作都经过这里。
#
#   bash scripts/github/bot.sh <dev|pm|review> gh <组> <动作> [参数...]
#   bash scripts/github/bot.sh <dev|pm|review> git fetch [origin] [--tags] [--prune]
#   bash scripts/github/bot.sh <dev|pm> git push [-u] origin <feat|fix>/<编号>-<短名>
#     dev = 开发用 App(开发、集成 Agent)   pm = PM 用 App(PM Agent)   review = 评审用 App(评审、测试 Agent)
#
# 只允许下面的操作(其他一律拒绝):
#   全部: gh issue view|list|comment, gh pr view|list|diff|checks|comment, gh label list, gh search issues|prs, gh release view|list,
#         gh run view|list, gh api(只读), git fetch
#   dev:    gh issue create|edit|close|reopen, gh pr create|edit, gh pr merge --squash, gh api 写 repos/<所有者>/<仓库>/milestones,
#           git push 功能分支
#   pm:     gh issue create|edit, gh pr review --comment(PM 验收), git push 功能分支(方案)
#   review: gh issue edit(只改 状态:方案中 / 状态:待定版 / 待回答 / 待人决定 / 阻塞,加 需人定版), gh pr review --approve|--request-changes|--comment,
#           gh issue create(标签正好是 类型:改进 + 需人定版,给 /architecture 用;服务器端的 gate 也把评审 App 建的 Issue 当作需人定版)
#   任何人: 不加、不去掉人专用标签(设计已批准、已验收、免验收),不去掉 需人定版
# 环境: 环境变量 BOT_ROLE 必须等于 <dev|pm|review>(一个环境只用一个身份);GH_TOKEN / GITHUB_TOKEN 有值时拒绝;
#       运行环境里只要能找到人的 GitHub 凭据(gh 的登录或 git 的凭据),就拒绝运行(引导手册 4 步)。
# 设置(只在 Agent 的运行环境里,不进 git): ${BOT_CONFIG_DIR:-$HOME/.github-bots/<owner>-<repo>}/<dev|pm|review>.env
#   A. 私钥在本机: APP_ID=<App 的 ID>   INSTALLATION_ID=<安装 ID>   PRIVATE_KEY_FILE=<App 私钥 .pem 的路径>
#      用私钥签 10 分钟有效的 JWT(openssl)→ 换一个只限本仓库、只给需要的权限、1 小时有效的安装令牌 → 只在这条命令里使用。
#   B. 令牌代理(推荐;私钥不在 Agent 能读的地方): BROKER_URL=http://127.0.0.1:<端口>   BROKER_SECRET_FILE=<口令文件>
#      向 scripts/github/token_broker.py 要令牌(口令只用标准输入交给 curl,不出现在命令行)。这时不能再写 PRIVATE_KEY_FILE。
# JWT、口令和令牌都不显示、不写进文件。BOT_DRY_RUN=1 时只做检查(A:JWT 签名验证;B:向代理取一次令牌),不运行命令(测试用)。
set -u
set -o pipefail

refuse() { echo "bot.sh: $1" >&2; exit 2; }
[ $# -lt 2 ] && refuse "用法: bash scripts/github/bot.sh <dev|pm|review> gh|git <参数...>"
role="$1"; shift
[[ "$role" =~ ^(dev|pm|review)$ ]] || refuse "身份只能是 dev、pm 或 review"
[ "${BOT_ROLE:-}" = "$role" ] || refuse "这个环境的 BOT_ROLE 是 ${BOT_ROLE:-(没设)},不能用 $role 的身份(一个环境只用一个身份)"
[ -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ] || refuse "环境变量 GH_TOKEN / GITHUB_TOKEN 有值:Agent 的环境里不放令牌"

top="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
py="${PYTHON:-python}"
cfg="$("$py" - "$top/project.toml" <<'PY'
import sys, tomllib
d = tomllib.load(open(sys.argv[1], "rb")).get("github", {})
print(d.get("owner", "")); print(d.get("repo", "")); print(len({d.get("dev_bot"), d.get("pm_bot"), d.get("review_bot")}))
PY
)" || refuse "读不了 project.toml"
cfg="$(printf '%s\n' "$cfg" | tr -d '\r')"
owner="$(sed -n 1p <<< "$cfg")"; repo="$(sed -n 2p <<< "$cfg")"
[ "$(sed -n 3p <<< "$cfg")" = 3 ] || refuse "dev_bot、pm_bot、review_bot 要是三个不同的 App(做的和审的必须分开)"

# ---- 允许的操作 -------------------------------------------------------------------------------------------------------------
labels_ok() {  # $1 = 只允许这些标签的正则(空 = 不限),其后是 gh 的参数;人专用标签和去掉 需人定版 一律不允许
  local only="$1"; shift; local prev="" a l
  for a in "$@"; do
    local op="" val=""
    if [[ "$prev" =~ ^(--(add|remove)-label|--label|-l)$ ]]; then op="$prev"; val="$a"
    elif [[ "$a" =~ ^-l(.+)$ ]]; then op="--label"; val="${BASH_REMATCH[1]}"
    elif [[ "$a" =~ ^(--(add|remove)-label|--label)=(.*)$ ]]; then op="${BASH_REMATCH[1]}"; val="${BASH_REMATCH[3]}"; fi
    if [ -n "$op" ]; then
      IFS=',' read -ra ls <<< "$val"
      for l in "${ls[@]}"; do
        [[ "$l" =~ ^(设计已批准|已验收|免验收)$ ]] && refuse "人专用标签($l)只由人加或去掉"
        [ "$op" = --remove-label ] && [ "$l" = 需人定版 ] && refuse "需人定版 只由人去掉"
        [ -z "$only" ] || [[ "$l" =~ $only ]] || refuse "身份 $role 不能改标签 $l"
      done
    elif [ -n "$only" ] && [[ "$a" == -* ]] && ! [[ "$a" =~ ^--(add|remove)-label$ ]]; then
      refuse "身份 $role 用 gh issue edit 只能改标签"
    fi
    prev="$a"
  done
}
case "${1:-}" in
  gh)
    group="${2:-}"; action="${3:-}"
    [[ "$group" == -* || "$action" == -* ]] && refuse "把选项放在 gh <组> <动作> 后面"
    allowed=0
    case "$group $action" in
      "issue view"|"issue list"|"issue comment"|"pr view"|"pr list"|"pr diff"|"pr checks"|"pr comment"|"label list"|"search issues"|"search prs"|\
      "release view"|"release list"|"run view"|"run list") allowed=1 ;;
      "issue close"|"issue reopen") [ "$role" = dev ] && allowed=1 ;;
      "pr create"|"pr edit") [ "$role" = dev ] && labels_ok "" "${@:4}" && allowed=1 ;;
      "issue create")
        labels_ok "" "${@:4}"
        if [ "$role" = review ]; then      # /architecture only: exactly the two labels below
          got=""; prev=""
          for a in "${@:4}"; do
            val=""
            if [[ "$prev" =~ ^(--label|-l)$ ]]; then val="$a"; elif [[ "$a" =~ ^(--label=|-l)(.+)$ ]]; then val="${BASH_REMATCH[2]}"; fi
            if [ -n "$val" ]; then
              IFS=',' read -ra ls <<< "$val"
              for l in "${ls[@]}"; do
                [[ "$l" =~ ^(类型:改进|需人定版)$ ]] || refuse "评审 App 建的 Issue 只能带 类型:改进、需人定版(收到 $l)"
                got="$got $l"
              done
            fi
            prev="$a"
          done
          [[ "$got" == *类型:改进* && "$got" == *需人定版* ]] || refuse "评审 App 建的 Issue 要带 类型:改进 和 需人定版"
        fi
        allowed=1 ;;
      "issue edit")
        if [ "$role" = review ]; then labels_ok '^(状态:方案中|状态:待定版|待回答|待人决定|阻塞|需人定版)$' "${@:5}"; else labels_ok "" "${@:4}"; fi
        allowed=1 ;;
      "pr merge")
        [ "$role" = dev ] || refuse "只有开发 App(集成 Agent)能合并"
        squash=0
        for a in "${@:4}"; do
          case "$a" in
            --squash|-s) squash=1 ;;
            --admin|--auto|--merge|-m|--rebase|-r|--disable-auto) refuse "合并只用 --squash(不许 $a)" ;;
          esac
        done
        [ $squash -eq 1 ] || refuse "合并要写 --squash"
        allowed=1 ;;
      "pr review")
        case "$role" in
          review) allowed=1 ;;
          pm) for a in "${@:4}"; do [[ "$a" =~ ^(--approve|-a|--request-changes|-r)(=.*)?$ ]] && refuse "PM App 只写评论型的评审(--comment)"; done
              allowed=1 ;;
          *) refuse "开发 App 不评审" ;;
        esac ;;
      api\ *)
        method="GET"
        for a in "${@:3}"; do
          [[ "$a" =~ ^(-f|-F|--field|--raw-field|--input)(=.*)?$ || "$a" =~ ^-[fF].+ ]] && method="POST"
        done
        nx=0
        for a in "${@:3}"; do [[ "$a" =~ ^(-X|--method)(=?.*)?$ ]] && nx=$((nx + 1)); done
        [ $nx -le 1 ] || refuse "gh api 的 -X / --method 只能写一次"
        [[ " ${*:3} " =~ \ (-X|--method)[\ =]?([A-Za-z]+) ]] && method="${BASH_REMATCH[2]^^}"
        path="$action"
        if [ "$method" = GET ]; then allowed=1
        elif [ "$role" = dev ] && [[ "$path" =~ ^/?repos/$owner/$repo/milestones(/[0-9]+)?$ ]]; then allowed=1; fi ;;
    esac
    [ $allowed -eq 1 ] || refuse "不允许的操作: gh $group $action(身份 $role)。见 bot.sh 开头的允许清单"
    ;;
  git)
    case "${2:-}" in
      fetch)
        for a in "${@:3}"; do [[ "$a" =~ ^(origin|--tags|--prune|-q|--quiet)$ ]] || refuse "git fetch 只允许 origin、--tags、--prune"; done ;;
      push)
        [ "$role" != review ] || refuse "评审 App 不推送"
        n=0
        for a in "${@:3}"; do
          if [[ "$a" =~ ^(-u|--set-upstream|origin)$ ]]; then continue; fi
          [[ "$a" =~ ^(feat|fix)/[0-9]+-[a-z0-9][a-z0-9-]*$ ]] || refuse "只能推送功能分支 feat|fix/<编号>-<短名>(收到: $a)"
          n=$((n + 1))
        done
        [ $n -eq 1 ] || refuse "git push 要写一个功能分支" ;;
      *) refuse "git 只允许 fetch 和 push" ;;
    esac ;;
  *) refuse "只能代理 gh 和 git(收到: ${1:-})" ;;
esac

# ---- 隔离: 不在有人的 GitHub 凭据的环境里运行 --------------------------------------------------------------------------------
if command -v gh >/dev/null 2>&1 && env -u GH_TOKEN -u GITHUB_TOKEN gh auth token --hostname github.com >/dev/null 2>&1; then
  refuse "这个环境里有人的 gh 登录。Agent 要在没有人的 GitHub 凭据的环境(另一个系统用户或容器)里运行(引导手册 4 步)"
fi
if printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never \
     git -c credential.interactive=never credential fill 2>/dev/null | grep -q '^password='; then
  refuse "这个环境里有人的 git 凭据(github.com)。Agent 要在没有人的 GitHub 凭据的环境里运行(引导手册 4 步)"
fi

# ---- 设置与 JWT ------------------------------------------------------------------------------------------------------------
dir="${BOT_CONFIG_DIR:-$HOME/.github-bots/$owner-$repo}"
envf="$dir/$role.env"
[ -f "$envf" ] || refuse "找不到 $envf(引导手册 4 步)"
APP_ID=""; INSTALLATION_ID=""; PRIVATE_KEY_FILE=""; BROKER_URL=""; BROKER_SECRET_FILE=""
while IFS='=' read -r k v; do
  v="${v%$'\r'}"; v="${v%\"}"; v="${v#\"}"
  case "$k" in APP_ID) APP_ID="$v" ;; INSTALLATION_ID) INSTALLATION_ID="$v" ;; PRIVATE_KEY_FILE) PRIVATE_KEY_FILE="$v" ;;
    BROKER_URL) BROKER_URL="$v" ;; BROKER_SECRET_FILE) BROKER_SECRET_FILE="$v" ;; esac
done < "$envf"

if [ -n "$BROKER_URL" ]; then
  # ---- B. 令牌代理 ------------------------------------------------------------------------------------------------------------
  [ -z "$PRIVATE_KEY_FILE" ] || refuse "用令牌代理时,$envf 里不写 PRIVATE_KEY_FILE(私钥只放在代理那边)"
  [[ "$BROKER_URL" =~ ^http://(127\.0\.0\.1|localhost):[0-9]+$ ]] || refuse "BROKER_URL 只能是 http://127.0.0.1:<端口>(口令不发到本机以外)"
  [ -f "$BROKER_SECRET_FILE" ] || refuse "找不到 BROKER_SECRET_FILE($BROKER_SECRET_FILE)"
  resp="$(printf 'Authorization: Bearer %s\n' "$(tr -d '[:space:]' < "$BROKER_SECRET_FILE")" | curl -sS --noproxy '*' -H @- "$BROKER_URL/token/$role")" \
    || refuse "连不上令牌代理 $BROKER_URL(代理在运行吗?)"
  token="$(printf '%s' "$resp" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)"
  if [ -z "$token" ]; then
    msg="$(printf '%s' "$resp" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("message",""))' 2>/dev/null)"
    unset resp; refuse "令牌代理没给令牌: ${msg:-未知的错误}"
  fi
  unset resp
  if [ "${BOT_DRY_RUN:-0}" = "1" ]; then
    echo "bot.sh: 令牌代理发了令牌(身份 $role)。dry-run:不运行: $*"
    exit 0
  fi
else
[[ "$APP_ID" =~ ^[0-9]+$ ]] && [[ "$INSTALLATION_ID" =~ ^[0-9]+$ ]] && [ -f "$PRIVATE_KEY_FILE" ] \
  || refuse "$envf 里 APP_ID / INSTALLATION_ID 要是数字,PRIVATE_KEY_FILE 要指向存在的文件(或改用令牌代理:BROKER_URL、BROKER_SECRET_FILE)"

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
now="$(date +%s)"
header="$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)"
claims="$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' "$((now - 60))" "$((now + 540))" "$APP_ID" | b64url)"
sig="$(printf '%s.%s' "$header" "$claims" | openssl dgst -sha256 -sign "$PRIVATE_KEY_FILE" -binary | b64url)" || refuse "用私钥签名失败"
[ -n "$sig" ] || refuse "用私钥签名失败(签名是空的)"

if [ "${BOT_DRY_RUN:-0}" = "1" ]; then
  tmpd="$dir/.verify.$$"; mkdir -p "$tmpd"; trap 'rm -rf "$tmpd"' EXIT
  openssl rsa -in "$PRIVATE_KEY_FILE" -pubout -out "$tmpd/pub.pem" 2>/dev/null
  printf '%s' "$sig" | tr -- '-_' '+/' | awk '{ n = length($0) % 4; if (n) $0 = $0 substr("===", 1, 4 - n); print }' \
    | openssl base64 -d -A > "$tmpd/sig.bin"
  if printf '%s.%s' "$header" "$claims" | openssl dgst -sha256 -verify "$tmpd/pub.pem" -signature "$tmpd/sig.bin" >/dev/null 2>&1; then
    echo "bot.sh: JWT 签名验证通过(App $APP_ID,安装 $INSTALLATION_ID)。dry-run:不连 GitHub,不运行: $*"
    exit 0
  fi
  echo "bot.sh: JWT 签名验证失败" >&2; exit 1
fi

# ---- 令牌(只限本仓库、只给需要的权限)与运行 ---------------------------------------------------------------------------------
if [ "$role" = review ]; then perms='{"contents":"read","issues":"write","pull_requests":"write","metadata":"read"}'
else perms='{"contents":"write","issues":"write","pull_requests":"write","metadata":"read"}'; fi
body="$(printf '{"repositories":["%s"],"permissions":%s}' "$repo" "$perms")"
resp="$(curl -sS -X POST -H "Authorization: Bearer $header.$claims.$sig" -H "Accept: application/vnd.github+json" \
  -d "$body" "https://api.github.com/app/installations/$INSTALLATION_ID/access_tokens")" || refuse "连接 GitHub 失败"
token="$(printf '%s' "$resp" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)"
if [ -z "$token" ]; then
  msg="$(printf '%s' "$resp" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("message",""))' 2>/dev/null)"
  unset resp; refuse "没拿到安装令牌: ${msg:-未知的错误}(检查 App 的 ID、安装 ID、权限、电脑的时间)"
fi
unset resp sig
fi
if [ "$1" = gh ]; then
  GH_TOKEN="$token" GH_REPO="$owner/$repo" "$@"
else
  # origin 是 SSH 地址时也改走 https(令牌只能用于 https)
  BOT_TOKEN="$token" GIT_TERMINAL_PROMPT=0 git -c credential.helper= \
    -c 'credential.helper=!f() { echo username=x-access-token; echo "password=$BOT_TOKEN"; }; f' \
    -c url.https://github.com/.insteadOf=git@github.com: -c url.https://github.com/.insteadOf=ssh://git@github.com/ "${@:2}"
fi
