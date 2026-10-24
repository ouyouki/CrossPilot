---
description: "为人退回的 PR 开撤回 PR(集成 Agent)。参数: <PR 编号>"
---
<!-- 由 scripts/dev/gen_adapters.py 从 commands/revert.md 生成。不要手改,改 commands/revert.md 后重新生成。 -->

用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `integrator`(subagent_type: integrator),把参数原样传过去,不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。

按 `agents/integrator.md` 的「/revert」处理 PR #$ARGUMENTS。
