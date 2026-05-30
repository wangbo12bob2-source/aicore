# Claude Code 包装层设计文档：aicore 项目级工作流壳 MVP

## 1. 背景

现有 `aicore` 已具备三类核心能力：

- 任务启动闸机：`start / review / approve / reject`
- 执行安全层：`log-write / checkpoint`
- 完成态账本：`ledger-confirm`

这些能力已经能通过 CLI 使用，但当前仍缺少一层面向 Claude Code 的项目级工作流包装。

缺少这层包装会导致几个现实问题：

- Claude Code 即使能写代码，也不会自然遵守 `aicore` 的时机约束
- 已做过的能力、踩过的坑和恢复点仍可能只存在聊天上下文里
- 换一个会话、换一个执行器、甚至换一个系统后，项目知识无法稳定复用

因此需要为 Claude Code 增加一层项目级包装，使其在当前项目内优先遵循 `aicore` 工作流。

## 2. 目标

本 MVP 只解决一件事：

> 让 Claude Code 在当前项目里拥有稳定、可执行、可复用的 `aicore` 操作入口，而不是只依赖临时聊天提醒。

具体目标：

1. 用项目级 `CLAUDE.md` 明确 `aicore` 触发规则
2. 用 `.claude/commands/` 提供显式命令入口
3. 用 `.claude/agents/` 提供一个以流程监督为主的最小 agent

## 3. 范围

### 3.1 本版本负责

- 为当前项目新增 Claude Code 项目级包装层
- 把 `aicore` 的 4 个关键动作暴露为 Claude Code command
- 提供一个最小 guard agent，用于监督是否漏掉关键流程动作
- 让 Claude Code 版包装层尽量复用现有 `aicore` CLI，而不是重写核心逻辑

### 3.2 本版本不负责

- 不重写 `aicore` 核心状态机
- 不把 `aicore` 变成完全自治 agent
- 不自动判断何时应该更新账本
- 不自动推断所有改动文件
- 不替代 Claude Code 自身的任务规划机制

## 4. 总体定位

Claude Code 版本第一版定位为：

> `aicore` 的项目级工作流壳（workflow wrapper）

它不是一个新的底层引擎，而是：

- 约束 Claude Code 的动作时机
- 提供标准命令入口
- 用最小 agent 做流程监督

## 5. 三层结构

第一版采用三层结构：

```text
CLAUDE.md
.claude/
  commands/
    aicore-start.md
    aicore-log-write.md
    aicore-checkpoint.md
    aicore-ledger.md
  agents/
    aicore-guard.md
```

### 5.1 `CLAUDE.md`

职责：

- 定义本项目内必须遵守的 `aicore` 流程规则
- 说明哪些时机必须先调用 `aicore`
- 把 “先冻结任务、再留痕、再打 checkpoint、最后写账本” 变成项目级默认行为

它负责“总规则”，不负责实现具体命令逻辑。

### 5.2 `.claude/commands/`

职责：

- 为 Claude Code 提供显式可调用的动作入口
- 将自然语言工作流映射成稳定的 `aicore` CLI 调用
- 降低用户每次都要重新组织命令参数的负担

它负责“动作入口”，不负责长期监督。

### 5.3 `.claude/agents/aicore-guard.md`

职责：

- 监督 Claude Code 是否漏掉关键流程动作
- 在合适时提醒下一步应该调用哪一个 `aicore` 命令
- 协助组织 command 输入，但不主动夺取执行权

它负责“流程监督”，不是重型自治 agent。

## 6. 4 个 command 的职责

### 6.1 `/aicore-start`

用途：

- 在开始一个新任务前调用
- 将自然语言需求收敛成 `task.yaml + brief.md`
- 阻止未建任务就直接进入代码修改

本质：

- 任务启动闸门

### 6.2 `/aicore-log-write`

用途：

- 在一轮文件修改后立即调用
- 将当前修改固化为事件和快照
- 防止改动未及时留痕后丢失

本质：

- 改动留痕入口

### 6.3 `/aicore-checkpoint`

用途：

- 在一轮相关修改达到稳定点后调用
- 将若干事件固化为阶段 checkpoint
- 为恢复和迁移提供稳定锚点

本质：

- 阶段稳定点入口

### 6.4 `/aicore-ledger`

用途：

- 当某个变化已成为当前系统事实时调用
- 将完成态写入 `system-ledger.md`
- 防止已完成能力在新会话中再次被重复开发

本质：

- 完成态确认入口

## 7. Guard Agent 设计

第一版 `aicore-guard` 的定位是：

> 流程监督为主，辅助执行为辅。

### 7.1 它应该做的事

- 提醒是否还没有 `aicore start`
- 提醒关键改动后是否还没有 `log-write`
- 提醒阶段稳定后是否适合打 `checkpoint`
- 提醒能力已生效但还未写入 `ledger`
- 协助把用户输入整理成 command 所需参数

### 7.2 它不应该做的事

- 不替用户自动批准任务
- 不自动决定哪些改动一定要写账本
- 不替代 `aicore` CLI 本身
- 不自行重构或扩展项目边界
- 不主动提交 Git 或修改无关文件

## 8. 数据流关系

Claude Code 包装层不引入新的事实源，只是调用现有 `aicore` 事实源：

```text
Claude Code
  -> CLAUDE.md 约束动作时机
  -> /commands 提供显式入口
  -> aicore-guard 监督是否漏动作
  -> aicore CLI 真正落盘
  -> .aicore/tasks / history / system-ledger
```

原则：

- 项目真相仍由 `aicore` 文件系统状态承载
- Claude Code 包装层不维护第二套状态
- 所有项目记忆都应回写到 `.aicore/` 体系

## 9. 设计原则

### 9.1 复用优先

Claude Code 包装层必须优先复用现有 `aicore` CLI，不得复制核心逻辑。

### 9.2 监督优先于自治

第一版 agent 以监督为主，避免再次引入“AI 自作主张”的风险。

### 9.3 命令一义

每个 command 只绑定一种流程语义：

- `start` 不顺手写账本
- `log-write` 不顺手打 checkpoint
- `ledger` 不顺手回填历史事件

### 9.4 项目级默认优于临时提醒

一旦某条流程对当前项目重要，就应写入 `CLAUDE.md` 或 command，而不是只靠聊天提醒。

## 10. 成功标准

本 MVP 达成以下条件即可视为成功：

- 当前项目存在 Claude Code 项目级 `CLAUDE.md` 包装层
- 当前项目存在 4 个 `aicore` commands
- 当前项目存在 1 个最小 guard agent
- Claude Code 可通过这些入口调用现有 `aicore` CLI
- 不新增第二套状态文件
- Claude Code 版包装层明确引导用户避免重复开发已完成能力

## 11. 后续版本边界

以下内容留给后续版本：

- 根据 diff 自动建议 `log-write` 文件列表
- 自动生成 ledger 候选条目
- 多 agent 分工协作
- 跨项目共享技能包
- 从项目级包装层抽成通用 Claude Code 插件

## 12. 结论

Claude Code 版本第一版的重点，不是重新实现 `aicore`，而是：

> 给 Claude Code 提供一层稳定的项目级工作流壳，让它也能服从同一套任务、留痕和完成态体系。

这样已经做过的能力、已经踩过的坑和已经确认的系统事实，才不会在换会话、换执行器或换系统时被重新开发一遍。
