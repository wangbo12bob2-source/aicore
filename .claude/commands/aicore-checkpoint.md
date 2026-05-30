# /aicore-checkpoint

## 何时使用

在一轮相关修改达到稳定点后使用，例如测试通过、迁移阶段完成、或一个可恢复里程碑出现时。

## 执行动作

以下示例使用项目当前约定的 Python 3.11 启动器；如果当前系统使用其他 Python 3.11 启动方式，只替换启动器，不改变 `aicore.cli` 参数语义。

```bash
python3.11 -m aicore.cli checkpoint <task-id> --event <event-id> --summary "<summary>"
```

可为多个事件重复传入 `--event`。

## 输出

- 第一行是 `checkpoint-id`
- 第二行是 checkpoint manifest 路径

## 不要

- 不要引用不存在的 event
- 不要跨 task 混用 event
- 不要把 checkpoint 当作完成态账本
