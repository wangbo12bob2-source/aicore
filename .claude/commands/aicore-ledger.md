# /aicore-ledger

## 何时使用

只有当已批准 plan 或 brief 中的计划项完成、验证通过，并成为当前系统事实时使用。

账本必须按计划项落账：先找到对应计划项，再把该计划项的完成结果写入 `capability`、`entrypoint`、`limit`、`compatibility`、`risk`。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

```bash
python3.11 -m aicore.cli ledger-confirm <task-id> --event <event-id> --capability "<capability>" --entrypoint "<entrypoint>" --limit "<limit>" --compatibility "<compatibility>" --risk "<risk>"
```

## 输出

- `.aicore/system-ledger.md`
- 简要说明新增的完成态事实对应哪一个计划项

## 不要

- 不要凭聊天记忆补账
- 不要记录临时试验
- 不要记录尚未验证生效的推测
- 不要记录未出现在已批准 plan 或 brief 中的计划外能力
- 不要使用多行字段污染账本结构
