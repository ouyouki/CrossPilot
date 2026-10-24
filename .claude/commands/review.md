---
description: "评审(评审 Agent)。参数: <Issue 编号> 方案 | <Issue 编号> 测试用例 | <PR 编号>"
---
<!-- 由 scripts/dev/gen_adapters.py 从 commands/review.md 生成。不要手改,改 commands/review.md 后重新生成。 -->

用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `reviewer`(subagent_type: reviewer),把参数原样传过去,不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。

按 `agents/reviewer.md` 评审:$ARGUMENTS(带「方案」是 D1,带「测试用例」是 D2,只有编号是 PR 的 D3)。
