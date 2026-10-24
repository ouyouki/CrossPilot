# 开发方法(skills)

Agent 在对应的步骤读这里的文件,照着做(`agents/` 里写了哪一步读哪个)。不依赖 harness 的 skill 功能:两种 harness 都是直接读文件。

| skill | 内容 | 谁用 |
|---|---|---|
| `tdd/` | 测试驱动开发:先写失败的测试,一次一小块;好测试和坏测试;什么时候用替身(mock) | 开发 |
| `diagnosing-bugs/` | 排查难的 bug:先造能稳定复现的检查手段,再缩小、假设、验证、修复、加回归测试 | 开发、测试、集成 |
| `codebase-design/` | 模块设计:接口小、里面深;边界(接缝)放在哪;为测试而设计;同一个接口设计两次再选 | 开发、评审 |
| `domain-modeling/` | 业务用语和设计决定:维护 `docs/术语表.md` 和 `docs/决策/` | PM、评审 |
| `prototype/` | 一次性原型:用一个 HTML 文件验证业务逻辑和状态,画面用方案套件 | PM |
| `research/` | 查一手资料(官方文档、源码、规格),每条结论注明出处 | PM、开发 |
| `pr/` | PR 正文的写法:概要、证据、合并风险 | 开发 |
| `code-review/` | D3 的两个方向:「规范」(仓库的规则 + 一组固定的坏味道)和「需求」(缺、多、错),分开写结论 | 评审 |
| `improve-architecture/` | 每周找"浅模块",写代码结构建议,最值得做的提成 Issue(需人定版) | 评审(`/architecture`) |
| `retro/` | 每周回顾运行记录,找反复出错或浪费的地方,提出改进(需人定版) | 集成(`/retro`) |
| `to-tickets/` | 一天做不完的需求拆成纵向切片的子 Issue,写明依赖 | PM |
| `to-questionnaire/` | 要问别人的问题做成问卷,由人转交 | PM |
| `grill-me/` | **人用**:提需求前让 AI 一轮轮追问,把想法问清楚 | 你自己的会话 |
| `to-spec/` | **人用**:把讨论整理成「需求」表单的内容,你确认后提交 | 你自己的会话 |
| `writing-for-agents/` | **人用**:改 `agents/`、`commands/`、`skills/`、`AGENTS.md` 时检查写法(指针、层次、做完的标准、删减) | 你自己的会话 |

## 出处

改编自 Matt Pocock 的 [skills](https://github.com/mattpocock/skills)(v1.3.1,MIT 许可,许可全文见 `LICENSE-mattpocock-skills.txt`)。
对应的原名:improve-architecture ← improve-codebase-architecture;grill-me ← grill-me + grilling;其他同名。
`pr/` 的原版注明:「概要」一节的图示清单几乎原样取自 Dex Horthy(HumanLayer)的 show-me skill(https://github.com/humanlayer/skills)。

改编的地方:译成中文;去掉"问用户"的步骤,改成按 Issue 上的记录判断、判断不了写 `[提问]`(Agent 在无人看管时运行);
用词和文件位置改成本框架的(`docs/术语表.md`、`docs/决策/`、`docs/changes/<编号>/`、用例 ID、D1〜D3);
去掉开多个子 Agent 并行的做法(费 Token)。原作者更新时,对照原文手动同步。
