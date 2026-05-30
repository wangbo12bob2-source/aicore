# /aicore-start

## 何时使用

在开始任何新的实现、修复、迁移或重构任务前使用。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

```bash
python3.11 -m aicore.cli start "<需求>"
```

## 输出

- 记录生成的 `task-id`
- 提醒用户查看 `.aicore/tasks/<task-id>/brief.md`
- 明确当前仍处于任务启动阶段

## 不要

- 不要在未生成任务草案前直接修改代码
- 不要在此命令中顺手执行实现
- 不要自动 approve
