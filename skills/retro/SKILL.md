---
name: retro
description: 定期回顾 Agent 这一周的运行记录(退回、阻塞、重试、Token、日志),找出让 Agent 反复出错或浪费的环境问题,提出改进(规则、自动检查、工具)。集成 Agent 在调度的 /retro(每周一次)时读。
---

# 回顾

> 改编自 Matt Pocock 的 skills(retro,MIT,见 `skills/LICENSE-mattpocock-skills.txt`)。原版回顾一个会话并讲给用户;本框架里回顾一周的运行记录,写成报告,最值得做的提成 Issue,做不做由人定版。

目的:改进 Agent 的**环境**(规则、检查、工具、文档),让以后的运行更好。不是评价某次的代码。

## 1. 读一手记录(上次 `[回顾]` 之后的)

- 本环境(开发环境)一周的运行记录 `tmp/agent-logs/runs.jsonl`(每次运行一行:命令、Issue、Token、退出码、用时、第几次重试;阻塞和跳过也各一行)
  和各次的日志 `tmp/agent-logs/<日期>/`。
  PM 环境和评审环境的日志在别的环境里,读不到;它们的情况从 GitHub 上的记录(下一条)看。
- GitHub 上的记录(`B gh …` 只读):
  - 评审的要求修改、`[测试-退回]`、`[PM-退回]`、`[评审-退回]` 的理由(`B gh pr list --state all --json number,reviews,comments` 等);
  - `[阻塞]` 评论和带 `阻塞` 的 Issue;
  - CI 失败的检查(`B gh run list --status failure --json …`、`B gh run view <编号> --log-failed`);
  - 最近一次变异测试(`B gh run list --workflow mutation.yml --limit 1 --json conclusion,url,createdAt`,失败时 `B gh run view <编号> --log-failed`):
    测试没发现的变异集中在哪些文件,就是测试只"跑过"、没真正检查的地方;
  - 人写的 `[退回]`、`[决定]`、对 `[回答]` 的纠正。
- 现在的规则和检查:`AGENTS.md`、`agents/`、`skills/`、`docs/运营规则.md`、`project.toml` 的 `[checks]`、`.github/workflows/`。

## 2. 找改进的候选(按这些类别)

- **找东西**:Agent 是不是花了很多轮才找到要的文件或信息?文件之间有看不出来的依赖吗?在 `AGENTS.md` 或某个 Agent 的定义里加一句"X 在哪里"能省事吗?
- **自动检查**:有没有 Agent 犯的错、本来可以被自动检查抓住(lint、类型检查、测试、文件位置的检查)?先读项目已有的检查命令和 CI;已经有但没接上或坏了的,这本身就是发现。项目没有 lint / 类型检查也是发现。
- **评审的规则**:评审 Agent 漏掉了什么?先分类:**机械的**(固定的写法、禁用的函数、import 的形式、文件位置)→ 做成自动检查(lint 规则、CI 的作业),不写成规则;**需要判断的**(跨文件的一致性、和周围风格一致)→ 加到 `agents/reviewer.md` 或对应的 `skills/`。
- **`AGENTS.md` 太长**:有没有该移到 Agent 定义、skill、自动检查里的指示?`AGENTS.md` 每个 Agent 都要读,应该很短,主要放"在哪里"。
- **Token 的消耗**:哪些运行特别贵(日志里 Token 多、轮数到上限、超时)?能少读文件、换更便宜的命令、缩小测试范围吗?`[runner]` 的上限合适吗?
- **无效的指示**:规则文件里有没有对 Agent 的行为没有影响的话?(太长时更要找)
- **拿不到的信息**:有没有关键信息 Agent 拿不到(服务的日志、只读访问外部服务)?

做的人(开发 Agent)压力最大:要探索、写代码、排查。评审 Agent 只看差异,压力小。所以**代码规范由评审来执行**,不加给开发 Agent。

## 3. 写报告

在「每日计划」Issue 写一条评论,第一行固定 `[回顾] YYYY-MM-DD`(日期按 `project.toml` 的 `utc_offset`)。没有值得提的也写 `[回顾] YYYY-MM-DD 本周没有`。
按严重程度排,每个候选:类别、证据(Issue / PR 编号、日志的位置、次数或 Token)、建议改哪个文件怎么改(一两句)。再写一行本周的概况:运行次数、Token、退回次数、阻塞次数。

## 4. 提成 Issue(最多 2 个)

最严重的最多 2 个提成 Issue。先搜已有的 `类型:改进`(**开着的和已关闭的都看**:`B gh issue list --state all --label 类型:改进 --json number,title,state`):
同样的主题已经有了就不提;人关闭了的(不做)除非有新的证据,也不再提。
`B gh issue create --title "[改进] <一句话>" --label 类型:改进 --label 需人定版 --body-file -`,
正文写目的、范围(要改的文件)、验收条件、来源(`[回顾] YYYY-MM-DD`)。
`需人定版` 一定要加。不加 `状态:待处理`:人看过后加上它,PM 才会拾取(不想做的直接关闭)。改 `AGENTS.md`、`agents/`、`skills/`、`scripts/`、`.github/` 这些框架文件的 PR 另外要人批准(CODEOWNERS)。
