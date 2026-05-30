# /aicore-save

## 何时使用

在 Claude Code 完成一轮文件修改后立即使用，尤其是容易被忽略的小改动。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

先记录本轮改动：

```bash
python3.11 -m aicore.cli log-write <task-id> --session <session-id> --file <path> --summary "<summary>"
```

拿到第一行 `event-id` 后，立即生成 checkpoint：

```bash
python3.11 -m aicore.cli checkpoint <task-id> --event <event-id> --summary "<summary>"
```

## 输出

- `event-id`
- `checkpoint-id`
- 事件文件路径和 checkpoint manifest 路径

## 不要

- 不写 ledger；账本只按已批准 plan 或 brief 的计划项完成结果落账
- 不要把未修改文件写入事件
- 不要在没有 task-id 时伪造任务边界
- 不要跳过 checkpoint
