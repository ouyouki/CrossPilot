// 命令监视(docs/运营规则.md 9 章):OpenCode 运行 bash 工具之前,把命令交给 scripts/dev/guard_bash.sh 判断,
// 它以退出码 2 结束时抛出错误,命令就不会运行。判断规则只有 guard_bash.py 一份(和 Claude Code 的 hook 共用)。
export const Guard = async ({ worktree, directory }) => {
  const root = worktree || directory
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return
      const command = (output && output.args && output.args.command) || ""
      const proc = Bun.spawnSync(["bash", `${root}/scripts/dev/guard_bash.sh`], {
        stdin: new TextEncoder().encode(JSON.stringify({ tool_input: { command } })),
        stdout: "ignore",
        stderr: "pipe",
      })
      if (proc.exitCode !== 0) {
        throw new Error(new TextDecoder().decode(proc.stderr) || "guard_bash: 已拦下这条命令")
      }
    },
  }
}
