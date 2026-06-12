# Claude Code 项目规则

## 事实源

- 本项目使用 `aicore` 作为唯一任务、历史、账本事实源。
- Claude Code 不维护第二套状态，不创建独立任务列表、历史记录或账本。

## 工作流程

- 任务开始前，必须先执行 `aicore start`。
- 对于 Vibe Coding 任务，开始前先对照 `docs/contracts/vibe-coding-contract.md` 检查任务边界。
- 改完文件后，必须执行 `/aicore-save`，一次完成 `log-write` 和 `checkpoint`。
- Claude Code 收到 PostToolUse 保存提醒后，必须先处理保存动作，再继续下一步。
- `ledger-confirm` 必须按已批准 plan 或 brief 中列出的计划项落账，不要凭聊天记忆补账。
- 只有计划项已完成、验证通过、且成为当前系统事实时，才可以进入 `ledger-confirm`。

## 协作规则

- 所有对话回答使用中文。
- 修改和设计必须兼容 macOS、Windows、Linux，不硬编码平台专属路径、分隔符、权限或可执行后缀。
- `aicore` 负责 Vibe Coding 的任务级架构审核、修改范围约束、验收依据和回退策略，不替代安全与架构专项审查。
