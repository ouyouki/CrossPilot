# CrossPilot

TikTok Shop 日本站（跨境直邮、单店）的自动运营系统。**AI 干活，人只做两件事：批，和给方向。**

本仓库按 PM Agent 框架运行：一个人只做判断（定版、验收、上线），PM、开发、集成、评审、测试五个 Agent 分工完成日常作业，所有协作走 GitHub（Issue、PR、评论、标签）。规则正本是 `docs/运营规则.md`，给 Agent 的入口是 `AGENTS.md`。

## 跑起来（本机）

```bash
# 1. 构建前端（第一次、或改了 frontend/ 之后）
cd frontend && npm install && npm run build && cd ..

# 2. 启动（只绑 127.0.0.1）
cd backend && python -m app.server
```

浏览器打开 **http://127.0.0.1:8000**：

- **今日**：待批数、开工前置清单、提醒
- **候选**：样例候选列表，点一行展开 16 项成本与毛利

> 装了 FastAPI 时也可以 `cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000`（接口相同；静态页仍由 `app.server` 那套逻辑提供）。样例数据在 `backend/data/sample/`，断网也能跑。

## 跑测试

```bash
cd backend && python -m unittest discover -s tests -t .
```

无第三方依赖、无需数据库、无需联网。

## 目录

| 路径 | 是什么 |
|---|---|
| `design/` | 产品设计书与画面原型（**只读依据**） |
| `backend/crosspilot/` | 确定性内核：`04` 审批闸门引擎 + `costing` 成本测算 |
| `backend/app/` | 应用骨架：只读接口（今日 / 候选）与静态页 |
| `backend/data/sample/` | 样例数据（不是平台事实） |
| `frontend/` | React 18 + Vite + TypeScript；样式复用 `design/screens/assets/cp2.css` 的令牌 |
| `docs/运营规则.md` | 流程正本 |
| `docs/changes/<编号>/` | 每个 Issue 的方案、设计、用例与证据 |
| `docs/交接.md` | 换机器继续工作的手顺 |
| `agents/`、`commands/`、`scripts/`、`skills/` | 框架：Agent 定义、闸门、调度、开发方法 |

## 当前进度

- ✅ PM Agent 框架（规则集、CI 六项、三个 App 身份）
- ✅ `04` 内核：注册表、Gatekeeper（三值/失败即 HOLD）、审批状态机、13 条 PC、授权清单、审计哈希链、Tool Gate
- ✅ 成本测算：c1–c16、逐项取整、缺项即 UNKNOWN（INV-10）
- ✅ 最小可跑骨架：今日页 + 候选页（样例数据）
- ⬜ 数据库与持久化、真实导入、审批动作、素材、上架

## 红线怎么落到代码里

| 红线 | 结构保证 |
|---|---|
| RL-1 未批不执行 | 唯一出口 `ToolGate.call`；批准绑定 `approval_id + subject_refs + payload_hash` 且 CAS 单次消费 |
| RL-2 默认无批准权 | `approver_kind='human'` 强制；Agent 白名单里没有 `approval.decide`；授权只能 `ACT-SELECT`、24h 生效、只收窄 |
| RL-3 判定不出自模型 | `Gatekeeper` 纯函数、无网络/模型/ORM import（AST 测试强制）；异常与过期即 `HOLD` |
