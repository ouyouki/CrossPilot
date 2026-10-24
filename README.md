# CrossPilot 实现工作区

TikTok Shop 日本站（跨境直邮、单店）的自动运营系统。设计依据在 `design/`，实现从确定性内核开始。

| 目录 | 是什么 |
|---|---|
| `design/` | 设计书与原型（**只读依据**，唯一实现根据是 `design/ai/00_AI读我.md`） |
| `backend/` | 实现代码。当前：`04` 审批与闸门引擎的确定性内核 + INV 测试 |
| `docs/design-gaps.md` | 设计内部冲突与未决问题（D-1…D-8，含 2 条需人拍板） |
| `evidence/` | 测试证据（`09 §1` 要求；没有证据不算完成） |
| `framework/` | 待放入（PMagent 理念框架） |

## 跑测试

```powershell
cd backend
python -m unittest discover -s tests -t .
```

无第三方依赖、无需数据库、无需联网。

## 当前进度

- ✅ `04` 内核：动作注册表、Gatekeeper（三值/失败即 HOLD）、审批状态机（无时间边）、13 条 PC、授权清单（只收窄/原子消费）、审计哈希链、Tool Gate（唯一出口）
- ✅ INV-1…9、11、12、16…21 共 17 条不变量测试全绿（77 个用例）
- ⬜ PostgreSQL DDL 与真实约束
- ⬜ `02` 的 43 个 CAP（选品/成本/素材/上架/运营）
- ⬜ REST/SSE、前端画面

## 红线怎么落到代码里

| 红线 | 结构保证 |
|---|---|
| RL-1 未批不执行 | 唯一出口 `ToolGate.call`；未登记动作不存在；批准绑定 `approval_id + subject_refs + payload_hash` 且 CAS 单次消费；执行前重算前置条件 |
| RL-2 默认无批准权 | `approver_kind='human'` 强制；Agent 白名单里没有 `approval.decide`；授权只能 `ACT-SELECT`、24h 生效、只收窄 |
| RL-3 判定不出自模型 | `Gatekeeper` 纯函数、无网络/模型/ORM import（AST 测试强制）；三值评估；异常与过期即 `HOLD` |
