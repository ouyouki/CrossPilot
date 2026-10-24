# CrossPilot

TikTok Shop 日本站（跨境直邮、单店）的自动运营系统。**AI 干活，人只做两件事：批，和给方向。**

本仓库按 PM Agent 框架运行：一个人只做判断（定版、验收、上线），PM、开发、集成、评审、测试五个 Agent 分工完成日常作业，所有协作走 GitHub（Issue、PR、评论、标签）。规则正本是 `docs/运营规则.md`，给 Agent 的入口是 `AGENTS.md`。

## 目录

| 路径 | 是什么 |
|---|---|
| `design/` | 产品设计书与画面原型（**只读依据**；唯一实现根据是 `design/ai/00_AI读我.md`） |
| `backend/` | 实现代码。当前：`04` 审批与闸门引擎的确定性内核 + INV 测试 |
| `docs/运营规则.md` | 流程正本：角色、检查点、标签、合并前检验、调度上限、验收与上线 |
| `docs/templates/` | 每个需求的文档模板（01 需求 / 02 设计 / 03 测试用例 / 04 证据 / 范围.txt，含 Excel 版） |
| `docs/changes/<编号>/` | 每个 Issue 的方案、设计、用例与证据（由 `scripts/design/new_proposal.py` 起） |
| `docs/术语表.md`、`docs/回归清单.md`、`docs/决策/` | 业务用语、回归场景、重要设计决定 |
| `docs/design-gaps.md` | 设计书内部冲突与未决问题（D-1…D-8，含 2 条需人拍板） |
| `docs/安装清单.md` | 框架安装的进度与待办（人做 GitHub 设置时看这个） |
| `agents/`、`commands/` | 5 个 Agent、12 个命令的定义（**唯一来源**；`.claude/`、`.opencode/` 由它生成） |
| `scripts/` | 调度、合并前检验、闸门、App 身份、方案套件、开发自查 |
| `skills/` | 15 个开发方法（TDD、排查、设计、评审、拆分、回顾…，改编自 Matt Pocock，MIT） |
| `evidence/` | 测试证据（没有证据不算完成） |
| `framework/` | 框架的分发副本，**不进 git**（`template/` 的内容已铺到根目录） |

## 跑测试

```bash
cd backend && python -m unittest discover -s tests -t .
```

无第三方依赖、无需数据库、无需联网。

## 当前进度

- ✅ PM Agent 框架已装到仓库（本地部分；GitHub 设置见 `docs/安装清单.md`）
- ✅ `04` 内核：动作注册表、Gatekeeper（三值/失败即 HOLD）、审批状态机（无时间边）、13 条 PC、授权清单（只收窄/原子消费）、审计哈希链、Tool Gate（唯一出口）
- ✅ INV-1…9、11、12、16…21 共 17 条不变量，77 个用例全绿
- ⬜ PostgreSQL DDL 与真实约束
- ⬜ `02` 的 43 个 CAP（选品/成本/素材/上架/运营）
- ⬜ REST/SSE、前端画面

## 红线怎么落到代码里

| 红线 | 结构保证 |
|---|---|
| RL-1 未批不执行 | 唯一出口 `ToolGate.call`；未登记动作不存在；批准绑定 `approval_id + subject_refs + payload_hash` 且 CAS 单次消费；执行前重算前置条件 |
| RL-2 默认无批准权 | `approver_kind='human'` 强制；Agent 白名单里没有 `approval.decide`；授权只能 `ACT-SELECT`、24h 生效、只收窄 |
| RL-3 判定不出自模型 | `Gatekeeper` 纯函数、无网络/模型/ORM import（AST 测试强制）；三值评估；异常与过期即 `HOLD` |
