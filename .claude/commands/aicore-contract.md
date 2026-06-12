# /aicore-contract

## 何时使用

在开始新的 Vibe Coding 任务前，或感觉任务边界、命名、返回结构、状态机、修改范围开始发散时使用。

## 执行动作

先阅读项目契约：

```bash
cat docs/contracts/vibe-coding-contract.md
```

更推荐直接运行任务级架构检查单：

```bash
python3.11 -m aicore.cli checklist <task-id>
```

然后基于输出检查当前任务是否已经明确：

- 主入口
- 兼容入口
- 是否双改
- 允许修改文件
- 验收依据
- 风险
- 回退方案

如果这些信息缺失，先运行：

```bash
python3.11 -m aicore.cli update <task-id> ...
```

## 输出

- 指出当前任务还缺哪些契约项
- 提醒先补 `update`，再继续实现或 `approve`

## 不要

- 不要把契约当作安全扫描器
- 不要把契约当作全局架构审计工具
- 不要在未明确边界前直接开写
- 不要让 Agent 自行脑补额外场景
