---
description: "开发一个 Issue 的下一步(开发 Agent)。参数: <Issue 编号>;每次只做一步"
---
<!-- 由 scripts/dev/gen_adapters.py 从 commands/dev.md 生成。不要手改,改 commands/dev.md 后重新生成。 -->

用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `developer`(subagent_type: developer),把参数原样传过去,不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。

按 `agents/developer.md` 处理 Issue #$ARGUMENTS,从「0. 判断从哪一步开始」做起。
