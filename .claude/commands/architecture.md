---
description: "每周的代码结构建议(评审 Agent)。没有参数"
---
<!-- 由 scripts/dev/gen_adapters.py 从 commands/architecture.md 生成。不要手改,改 commands/architecture.md 后重新生成。 -->

用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `reviewer`(subagent_type: reviewer),把参数原样传过去,不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。

按 `agents/reviewer.md` 的「/architecture」处理。
