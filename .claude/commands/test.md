---
description: "独立测试一个 PR(测试 Agent)。参数: <PR 编号>"
---
<!-- 由 scripts/dev/gen_adapters.py 从 commands/test.md 生成。不要手改,改 commands/test.md 后重新生成。 -->

用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `tester`(subagent_type: tester),把参数原样传过去,不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。

按 `agents/tester.md` 测试 PR #$ARGUMENTS。
