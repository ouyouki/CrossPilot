# CrossPilot · backend

实现了 `design/ai/04_审批与闸门引擎.md` 的**确定性内核**（第一切片）。不含 API、数据库、前端与素材生成。

## 怎么跑

```powershell
cd backend
python -m unittest discover -s tests -t .
```

只用标准库（`unittest`），**没有运行期依赖**——这是设计要求的：判定路径不得依赖 LLM / 网络 / ORM（INV-8），所以它也不需要 `pip install` 任何东西。Python ≥ 3.12（设计写 3.12，本机实测 3.14 亦可）。

## 目录

| 路径 | 对应设计 | 内容 |
|---|---|---|
| `crosspilot/core/` | 01 §5、04 §3.1 | `Decision` / `Verdict` / `Facts` / `Actor` / 金额与 JCS 规范化 / 可注入时钟 |
| `crosspilot/registry/actions.py` | 04 §2、05 §3 | 动作注册表、工具目录、Agent×工具白名单、禁止存在的动作名 |
| `crosspilot/gatekeeper/` | 04 §3 | 三值规则、规则库新鲜度、`judge()`（纯函数） |
| `crosspilot/approvals/` | 04 §4–§5 | 审批单（不可变）、状态机（无时间边）、13 条 PC-* 前置条件、决策服务 |
| `crosspilot/grants/` | 04 §7 | 授权清单：24h 生效、只收窄、原子消费、包络匹配、抽检暂停 |
| `crosspilot/audit/` | 04 §12 | 只追加哈希链审计（含被拒调用） |
| `crosspilot/toolgate/` | 04 §1、§5.2 | 唯一出口：身份 → 注册表 → 授权 → 判定 → 绑定+CAS → 执行 → 审计 |
| `tests/` | 09 §2 | 每条不变量一个文件，文件名含 INV 号 |

## 三条实现的硬规矩

1. **判定路径没有依赖**：`gatekeeper/`、`grants/`、`approvals/preconditions.py` 不得 import 网络/模型/数据库模块；`tests/test_inv_08_*` 用 AST 扫描强制。
2. **异常即 HOLD**：`judge()` 的 `except` 返回 `HOLD`，`Decision` 里没有“UNKNOWN 通过”这个成员，写不出来。
3. **不猜未知项**：缺事实 → `missing_facts` → `HELD_UNKNOWN`；设计里的 U-* 在本层表现为“事实缺失”，不是默认值。

## 本切片**还没做**的

- PostgreSQL DDL 与真实约束（复合外键、状态转换触发器、部分唯一索引）：当前用内存实现等价语义，见 `docs/design-gaps.md`。
- INV-10 / 13 / 14 / 15：分别属成本测算、Agent 治理、素材版本、读回核对，随对应 CAP 落地。
- REST/SSE（07）、前端（08）、素材生成（03 §5）、连接器（13）。

## 证据

`evidence/04-engine/2026-10-24.md`。
