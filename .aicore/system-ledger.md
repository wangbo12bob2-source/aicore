## Current Capabilities
- Claude Code 可通过项目级 CLAUDE.md、四个 aicore slash command 和 aicore-guard 使用现有 aicore 工作流 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529110645062460-364781a1)
- Claude Code 在 Write/Edit/MultiEdit 后会通过 PostToolUse hook 主动提醒运行 /aicore-save，/aicore-save 一次完成 log-write 和 checkpoint (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529114309225882-7ababe19)
- aicore status 可从 .aicore/history 推导多工具 session、未 checkpoint event 和多 session 同文件修改风险 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260530063206193109-e421b4aa)

## Entrypoints
- CLAUDE.md；.claude/commands/aicore-start.md；.claude/commands/aicore-log-write.md；.claude/commands/aicore-checkpoint.md；.claude/commands/aicore-ledger.md；.claude/agents/aicore-guard.md (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529110645062460-364781a1)
- .claude/settings.json；.claude/hooks/aicore_save_reminder.py；.claude/commands/aicore-save.md (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529114309225882-7ababe19)
- python3.11 -m aicore.cli status (来源: task-2026-05-29-claude-wrapper-mvp / event-20260530063206193109-e421b4aa)

## Limits And Boundaries
- 当前 wrapper 只做流程薄包装，不自动批准、不自动提交 Git、不维护第二套状态 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529110645062460-364781a1)
- 主动保存只覆盖历史事件和 checkpoint；ledger-confirm 必须按已批准 plan 或 brief 的计划项完成结果落账 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529114309225882-7ababe19)
- 第一版 status 只读历史事件和 checkpoint，不做锁定、自动合并或阻止写入 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260530063206193109-e421b4aa)

## Compatibility
- 命令示例使用 Python 3.11 启动器约定；macOS、Windows、Linux 可替换为当前系统等价 Python 3.11 启动方式 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529110645062460-364781a1)
- hook 默认使用 python3.11 启动器；Windows 原生环境可替换为 py -3.11，脚本路径和 aicore 参数语义不变 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529114309225882-7ababe19)
- status 仅读取 JSON 历史文件，兼容 macOS、Windows、Linux 的项目工作区 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260530063206193109-e421b4aa)

## Known Risks
- aicore start 当前尚不能稳定识别 claude-wrapper 模块，后续应补模块识别后再强制完整 start 流程 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529110645062460-364781a1)
- Claude Code hooks 只能提醒并影响后续模型行为，不能替代用户对计划项完成态和账本内容的最终确认 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260529114309225882-7ababe19)
- 多 session 风险基于历史事件推导，不能替代人工 diff 检查或 Git merge 冲突处理 (来源: task-2026-05-29-claude-wrapper-mvp / event-20260530063206193109-e421b4aa)
