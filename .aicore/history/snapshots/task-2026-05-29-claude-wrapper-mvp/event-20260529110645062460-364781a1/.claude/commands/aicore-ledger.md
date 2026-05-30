# /aicore-ledger

## 何时使用

只有当用户或验证结果确认某个变化已经成为当前系统事实时使用。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

```bash
python3.11 -m aicore.cli ledger-confirm <task-id> --event <event-id> --capability "<capability>" --entrypoint "<entrypoint>" --limit "<limit>" --compatibility "<compatibility>" --risk "<risk>"
```

## 输出

- `.aicore/system-ledger.md`
- 简要说明新增的完成态事实

## 不要

- 不要记录临时试验
- 不要记录尚未验证生效的推测
- 不要使用多行字段污染账本结构
