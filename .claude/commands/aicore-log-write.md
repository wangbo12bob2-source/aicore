# /aicore-log-write

## 何时使用

在 Agent 完成一轮文件修改后立即使用。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

```bash
python3.11 -m aicore.cli log-write <task-id> --session <session-id> --file <path> --summary "<summary>"
```

可为多个文件重复传入 `--file`。

## 输出

- 第一行是 `event-id`
- 第二行是事件文件路径
- 提醒用户保留 `event-id`，后续 checkpoint 和 ledger 会引用它

## 不要

- 不要把未修改的文件写入事件
- 不要把临时失败试验当成完成态事实
- 不要在此命令中自动写 ledger
