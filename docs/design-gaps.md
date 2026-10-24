# 设计与实现的差异登记

> 依据 `design/ai/00_AI读我.md` §4：“看不懂的地方先在 `design/ai/` 里找答案，找不到就写成 `U-*` 提问，不要自己拍板。”
> 下面每条都标了**怎么处置**与**是否还需要人拍板**。冲突处理顺序：01 红线 > 04 引擎 > 其余。

## D-1 · “同意 2”到底叫什么动作

| 项 | 内容 |
|---|---|
| 位置 | `04 §2.1` vs `04 §4.2` |
| 冲突 | §2.1 声明 `ACT-APPROVE-ASSETS` **只是别名**、注册表不单列；§4.2 的“固定证据类型”表却以 `ACT-APPROVE-ASSETS` 为行键列了 6 类证据。 |
| 处置 | 注册表只存 `ACT-LIST-CREATE`；`registry.actions.evidence_kinds()` 把别名解析到真实动作。已测（`test_registry_contract.py`）。 |
| 影响 | 生成同意 2 审批单时必须用 `ACT-LIST-CREATE` 取证据；用别名取也会返回同一份，但**不能**把别名写进注册表（INV-12 会失败）。 |
| 待确认 | 否（实现已按“别名”处理，符合 §2.1 的明文声明） |

## D-2 · 06 §7 的审批人 `CHECK` 会让系统无法作废审批单

| 项 | 内容 |
|---|---|
| 位置 | `06 §7` DDL vs `04 §5.3` 状态机 |
| 冲突 | DDL 写 `CHECK (status IN ('DRAFT','PENDING') OR ((approver_user_id IS NULL) <> (delegated_via_grant_id IS NULL)))`；但 `VOID`（前置失效）与 `SUPERSEDED`（被新单取代）是**系统**事件，没有批准人也没有授权，两个字段都为空 → 约束失败。 |
| 处置 | 应用层对 `DRAFT/PENDING/VOID/SUPERSEDED` 豁免该检查（`approvals/model.py::_NO_DECIDER_STATUSES`），其余状态仍强制“恰好一个”。 |
| 影响 | 落 PostgreSQL 时必须把 DDL 改成 `status IN ('DRAFT','PENDING','VOID','SUPERSEDED') OR ((…))`，否则第一次 `VOID` 就写不进去。 |
| 待确认 | **是**（需要设计侧修 06 §7 的 DDL；本实现不会自行放宽到“任意状态都允许无批准人”） |

## D-3 · 清单在批准前到底能不能下载

| 项 | 内容 |
|---|---|
| 位置 | `05 §3` 工具目录 vs `04 §5.2` P0-6 |
| 冲突 | 05 把 `listing.build_checklist` 映射到 `ACT-BUILD-CHECKLIST`（AUTO）；04 §5.2 明写“**批准前清单与素材包不可下载**”。若按 AUTO 实现，Agent 可以在没有同意 2 的单子时先生成清单。 |
| 处置 | 按更严的一条（00 §2）：该工具映射到 `ACT-LIST-CREATE`（HUMAN_APPROVAL），“清单发放 = 执行”。`ACT-BUILD-CHECKLIST` 仍登记为打包动作。 |
| 影响 | 调用该工具必须带 `approval_id`、`subject_refs` 与 `payload_hash`，否则 `NOT_APPROVED` / `APPROVAL_MISMATCH`。已测（INV-1、INV-17）。 |
| 待确认 | 建议确认：是否把“生成清单文件（本地、无外部副作用）”与“发放/可下载”拆成两个动作 |

## D-4 · 导入动作的发起者

| 项 | 内容 |
|---|---|
| 位置 | `05 §3.1` 白名单矩阵 vs `04 §2.1` |
| 冲突 | 矩阵给 Scout 勾了 `import.parse_file` / `import.vision_extract`，但这两个工具对应的 `ACT-IMPORT-DATA` 是 `HUMAN_INITIATED`（“只有人能发起”）。 |
| 处置 | 按 04 执行：`HUMAN_INITIATED` 一律拒绝 Agent（INV-19）。人上传文件后由人/系统触发解析。 |
| 影响 | Scout 目前**不能**自己解析导入文件；这正好符合 05 §3 对 `import.parse_file` 的备注“系统（人上传后触发）”。 |
| 待确认 | 是否把“人上传（HUMAN_INITIATED）”与“解析（AUTO）”拆成两个动作，让 Scout 能解析已上传的批次 |

## D-5 · `OUTCOME_UNKNOWN` 没有出边（Q-01）

| 项 | 内容 |
|---|---|
| 位置 | `04 §5.3` |
| 冲突 | 状态机定义了 `EXECUTING → OUTCOME_UNKNOWN`（外部调用超时、结果不明），但没有定义从 `OUTCOME_UNKNOWN` 出来的边。 |
| 处置 | 本切片把它做成**终态**：`TRANSITIONS[OUTCOME_UNKNOWN] = frozenset()`，并在 `test_inv_02` 断言。 |
| 理由 | 若允许它自动转 `EXECUTED`，等于让“结果不明”自己变成“成功”，违反 RL-1；若允许直接重试，可能重复上架（通道 B）。 |
| 待确认 | **是（Q-01）**：建议只允许 `OUTCOME_UNKNOWN → VOID`（读回后由人开新单）；在答复前保持终态 |

## D-6 · 发布门槛的 INV 范围

| 项 | 内容 |
|---|---|
| 位置 | `09 §6` vs `01 §5` |
| 冲突 | 门槛写 “INV-1…INV-16 全绿”，但 `01 §5` 已有 INV-17…INV-21，且 AC-42/43/44 标 ★ 必须自动化。 |
| 处置 | 按更严取：门槛按 INV-1…INV-21。 |

## D-7 · INV 编号顺序

`01 §5` 把 INV-17…21 排在 INV-16 之前，`09 §3` 的 AC-32 排在 AC-44 之后。纯排版问题，不影响内容，建议修订时顺手排序。

## D-8 · 方向卡“保存即生效” vs 24 小时延迟

| 项 | 内容 |
|---|---|
| 位置 | `02 §4.1`（CAP-DIR-01/02）、`03 §2.1` 说保存生成新版本、收紧即时；`04 §8` 说方向卡的**放宽**也走 `pending_changes` 24 小时。 |
| 处置 | 以 04 为准（04 > 其余）。本切片只实现“收紧即时 + 放宽必须新建”，`pending_changes` 的 24 小时延迟属于后续切片，**尚未实现**。 |
| 待确认 | 否（方向已由 04 §8 明确） |

---

## 已知未验证项（不是设计冲突，是切片边界）

| 项 | 现状 | 何时关闭 |
|---|---|---|
| PostgreSQL 真实约束（复合外键 `(id, kind)`、状态转换触发器、未结单部分唯一索引、审计表撤权） | 用内存实现等价语义；DDL 未写、未在 PG 上跑 | 持久化切片 |
| INV-10（利润不可算 → 不进同意 1） | 成本测算未实现 | 选品/成本切片 |
| INV-13（同一 Agent 7 天 3 次未上报挂起 → SUGGEST_ONLY） | Agent 治理未实现 | 编排切片 |
| INV-14（已批素材改一像素 → 新版本） | 素材工厂未实现 | 素材切片 |
| INV-15（通道 A 回填实际值） | 上架/读回未实现 | 上架切片 |
