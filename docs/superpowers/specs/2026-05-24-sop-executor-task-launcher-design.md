# SOP 执行器设计文档：任务启动器 MVP

## 1. 背景与目标

本项目的第一版定位为 `SOP 执行器`，而不是通用 AI 编程代理或全自动工程系统。

它要解决的问题不是“让模型写更多代码”，而是“让 AI 在开始动手之前，先把任务边界、约束和验收标准收敛清楚，并且强制进入人工确认环节”。

第一版只聚焦一个阶段：`任务启动`。

目标是把一段自然语言需求转换为一份：

- 可机读的任务对象
- 可人读的启动说明
- 带明确状态的待审批草案

从而防止以下常见问题在任务一开始就发生：

- 上下文污染
- 需求理解漂移
- 顺手扩写范围
- 隐式跳过约束
- 未确认就进入执行

## 2. 范围定义

### 2.1 本版本负责

第一版负责：

- 接收一段自然语言需求
- 生成任务草案
- 生成结构化任务文件与人类可读说明
- 冻结最小项目上下文（项目类型、入口、允许修改范围、验收依据、回退方案）
- 记录任务在启动阶段的状态变化
- 在人工批准前阻止任务进入后续执行阶段

### 2.2 本版本不负责

第一版不负责：

- 直接改代码
- 自动执行测试
- 自动生成或执行完整编码会话
- 自动提交 Git
- 自动选择模型
- 自动拆分完整任务树
- 自动扫描整个仓库并推断全部上下文

这些能力属于后续版本，不纳入本次 MVP。

## 3. 产品定位

第一版产品定位为：`任务启动闸机`。

它不是一个负责完成开发任务的代理，而是一个负责在任务开始前冻结边界、显式记录约束、并要求人工审阅的流程系统。

其核心原则是：

- 未批准的任务不能进入执行
- 已批准的任务不得静默原地修改
- 任务变更通过新版本体现，而不是覆盖旧版本

## 4. 状态机设计

第一版状态机仅覆盖“任务启动阶段”，不覆盖实现、测试、发布等后续生命周期。

### 4.1 状态定义

支持以下五个状态：

1. `draft`
   刚由自然语言需求生成，尚未进入人工确认。

2. `reviewing`
   用户正在审阅任务启动包，可能进行补充或修订。

3. `approved`
   任务边界、约束和验收条件已获确认，可作为下游执行输入。

4. `rejected`
   当前草案被废弃，不再继续推进。

5. `superseded`
   当前版本被新版本替代，不再作为当前有效任务。

### 4.2 状态流转规则

允许的典型流转：

- `draft -> reviewing`
- `draft -> approved`
- `reviewing -> approved`
- `draft -> rejected`
- `reviewing -> rejected`
- `draft/reviewing -> superseded`

约束规则：

- `approved` 为冻结状态，后续若需求变化，应创建新版本
- 已有后继版本被批准时，旧版本可进入 `superseded`
- `rejected` 不能重新进入 `approved`
- `superseded` 不得再作为活跃任务使用
- 非法状态切换必须显式报错，不能静默忽略

## 5. 核心对象模型

第一版使用 `task.yaml` 作为单一事实源。

`brief.md`、终端摘要以及后续其他视图均由 `task.yaml` 派生。

### 5.1 最小数据结构

```yaml
id: task-2026-05-24-001
version: 1
status: draft

request:
  raw: "实现 JWT 登录"

project:
  type: product-delivery

scope:
  module: auth-login
  goal: "提供基于 JWT 的登录能力"
  in_scope:
    - "登录接口"
    - "密码校验"
    - "JWT 签发"
  out_of_scope:
    - "注册流程"
    - "refresh token"
    - "前端页面改造"

entrypoints:
  main:
    - "api/auth"
  compat: []

implementation:
  dual_write_required: false
  dual_write_reason: ""

change_scope:
  allowed_files: []
  protected_areas: []

constraints:
  platform:
    - macos
    - windows
    - linux
  rules:
    - "所有对话回答使用中文"
    - "不硬编码路径分隔符、系统路径、权限、可执行后缀"
    - "只做必要修改"
    - "不要顺手重构无关代码"
    - "遵循现有代码风格"
    - "先读后写"
    - "人工确认前不得进入下一步"

acceptance:
  success_criteria:
    - "存在明确的登录入口"
    - "密码校验路径清晰"
    - "JWT 生成逻辑被定义"
    - "相关测试范围被说明"
  baseline_refs: []

context:
  related_files: []
  related_modules: []
  assumptions: []
  risks: []
  rollback_plan: ""

review:
  summary: ""
  approved_by: null
  approved_at: null
  rejected_reason: null

history:
  created_at: "2026-05-24T10:00:00+08:00"
  updated_at: "2026-05-24T10:00:00+08:00"
  supersedes: null
  superseded_by: null
```

### 5.2 字段原则

- `request.raw` 必须保留用户原始输入，不能被覆盖
- `project.type` 用于标记任务属于产品化交付、逆向还原或混合迁移中的哪一类，以决定启动包的审阅重点
- `scope` 表达任务边界，而不是实现细节
- `out_of_scope` 是第一版重点字段，用于限制模型扩写范围
- `entrypoints` 必须显式记录主入口与兼容入口，避免多入口项目在新会话中丢失上下文
- `implementation.dual_write_required` 用于声明是否存在双实现同步义务；若为 `false` 但项目存在兼容入口，应在 `dual_write_reason` 中说明原因
- `change_scope.allowed_files` 与 `change_scope.protected_areas` 用于冻结允许修改范围和禁止修改范围
- `constraints` 需要显式注入项目级规则和跨平台要求
- `acceptance` 负责把任务从“需求摘要”提升为“可验收对象”
- `acceptance.baseline_refs` 用于引用验收依赖的基线文档、输出文件或回归脚本；若当前任务不依赖既有基线，可为空
- `review` 记录人工决策
- `context.rollback_plan` 记录本轮任务失败时的最小回退方案
- `history` 用于版本替代与追溯
- 所有会修改 `task.yaml` 的命令都必须同步更新 `history.updated_at`

### 5.3 暂不纳入的数据

第一版不纳入以下字段：

- `assigned_model`
- `estimated_tokens`
- `git_commit`
- `execution_steps`
- `test_results`

这些字段属于后续执行阶段，不应污染启动阶段对象。

## 6. CLI 设计

第一版 CLI 仅暴露四个核心命令：

1. `start`
2. `review`
3. `approve`
4. `reject`

### 6.1 `start`

用途：根据自然语言需求创建任务草案。

示例：

```bash
aicore start "实现 JWT 登录"
```

若基于旧任务创建新版本：

```bash
aicore start "补充 JWT refresh token 约束" --supersedes task-2026-05-24-001
```

行为：

- 创建任务目录
- 写入 `task.yaml`
- 渲染 `brief.md`
- 设置状态为 `draft`
- 提示用户补全或确认项目类型、主入口、兼容入口、允许修改范围、禁止修改范围、验收依据与回退方案
- 若提供 `--supersedes`，则新任务的 `history.supersedes` 指向旧任务 ID
- `start` 只负责创建后继草案，不会立即把旧任务置为 `superseded`
- 输出任务 ID、状态、生成文件路径和下一步建议

### 6.2 `review`

用途：查看任务启动包，并进入审阅态。

示例：

```bash
aicore review task-2026-05-24-001
```

行为：

- 读取 `task.yaml`
- 展示核心摘要
- 提示查看 `brief.md`
- 若当前为 `draft`，切换到 `reviewing`
- 若当前已是 `reviewing`，保持原状态
- 若状态发生变化，必须同步回写 `task.yaml` 并重新渲染 `brief.md`

### 6.3 `approve`

用途：人工批准任务草案。

示例：

```bash
aicore approve task-2026-05-24-001 --by "dong1"
```

行为：

- 仅允许从 `draft` 或 `reviewing` 进入 `approved`
- `--by` 为必填参数，用于显式记录批准人，避免依赖不同操作系统上的用户名推断
- 写入 `approved_by` 与 `approved_at`
- 冻结当前版本
- 若当前任务的 `history.supersedes` 非空，则在本次批准成功后，将被替代任务原子性地置为 `superseded`，并把其 `history.superseded_by` 回填为当前任务 ID
- `approve` 完成后必须重新渲染当前任务的 `brief.md`
- 明确提示后续变更需通过新版本处理

### 6.4 `reject`

用途：废弃当前任务草案。

示例：

```bash
aicore reject task-2026-05-24-001 --reason "边界不清晰"
```

行为：

- 状态置为 `rejected`
- 记录拒绝原因
- 保留现有文件用于审计与追溯
- 不允许再进入 `approved`
- `reject` 完成后必须重新渲染 `brief.md`

## 7. 文件布局

第一版建议固定如下目录结构：

```text
.aicore/
  tasks/
    task-2026-05-24-001/
      task.yaml
      brief.md
```

设计考虑：

- 兼容 macOS、Windows、Linux
- 每个任务天然隔离
- 方便后续新增 `events.log`、`prompt.md`、`checklist.md`

## 8. 任务启动流水线

当用户执行：

```bash
aicore start "实现 JWT 登录"
```

第一版内部按以下八步处理：

### 8.1 接收原始需求

保存用户原文到 `request.raw`，保证可追溯性。

### 8.2 提炼任务目标

将自然语言需求收敛成稳定的 `scope.goal`。

要求是清晰、克制、不过度扩展。

### 8.3 识别项目类型

根据现有仓库形态、任务描述和已知上下文，将任务初步归类为：

- `product-delivery`
- `reverse-engineering`
- `hybrid-migration`

若当前信息不足以可靠判断项目类型，应把不确定性写入 `assumptions` 或 `risks`，并在 `brief.md` 中明确提示人工确认。

### 8.4 推断模块归属

第一版使用轻量规则：

- 根据关键词推断模块名
- 若项目中已有模块目录或任务索引，优先匹配既有模块
- 若需求已能稳定收敛到单一逻辑模块，但仓库内暂无可匹配对象，则生成临时模块标识
- 若连“单一逻辑模块”都无法判断，则视为启动失败，而不是生成临时模块标识

### 8.5 冻结入口与修改边界

生成或要求人工补充：

- `entrypoints.main`
- `entrypoints.compat`
- `implementation.dual_write_required`
- `implementation.dual_write_reason`
- `change_scope.allowed_files`
- `change_scope.protected_areas`

其中：

- 若存在多入口或双实现风险，必须明确主入口与兼容入口
- 若当前任务不要求双改，必须说明不双改的原因
- 若允许修改范围暂时无法精确列出，应至少明确禁止修改范围和原因

### 8.6 生成边界定义

生成：

- `in_scope`
- `out_of_scope`
- `assumptions`
- `risks`

这是第一版最关键的任务解释动作。

### 8.7 注入项目级约束

将项目级规则显式写入 `constraints`，包括：

- 中文输出
- 跨平台兼容要求
- 不硬编码路径分隔符、系统路径、权限、可执行后缀
- 只做必要修改
- 先读后写
- 审批前不得进入下一步

### 8.8 写入验收依据、回退信息并落盘

补充或生成：

- `acceptance.success_criteria`
- `acceptance.baseline_refs`
- `context.rollback_plan`

要求：

- 若任务依赖既有基线、回归脚本或认可产物，必须在 `baseline_refs` 中显式引用
- 若本轮任务会影响入口、驱动、配置或多文件联动，必须写出最小回退方案
- 若回退方案仍不明确，应在 `risks` 中暴露，而不是省略

然后同时输出：

- `task.yaml`
- `brief.md`

最终状态设为 `draft`。

## 9. 失败策略

第一版必须显式暴露不确定性，不能伪装“理解成功”。

### 9.1 可生成草案

若需求可大致收敛，但仍存在模糊项，应允许生成 `draft`，并把不确定项写入：

- `assumptions`
- `risks`

以下信息若暂时只能部分判断，也允许先生成 `draft`，但必须在 `brief.md` 中高亮提示人工补充或确认：

- `project.type`
- `entrypoints`
- `change_scope.allowed_files`
- `acceptance.baseline_refs`
- `context.rollback_plan`

### 9.2 应拒绝生成完整草案的情况

若出现以下情况，应失败并要求补充信息，而不是强行生成完整任务：

- 需求过大，包含多个独立子系统
- 目标存在明显冲突
- 无法判断单一逻辑模块归属
- 涉及明显多入口或双实现联动，但无法确认主入口或本轮是否需要双改
- 涉及高风险入口、驱动或配置切换，但无法给出最小回退方案

失败信息需要明确说明原因，而不是给出空泛提示。

## 10. 成功标准

本 MVP 达成以下条件即可视为成功：

- 用户可通过一句自然语言需求启动任务
- 系统能生成结构化任务对象和人类可读说明
- 任务在批准前保持非执行状态
- 审批动作有明确状态变更记录
- 非法状态转换会显式报错
- 输出结果显式继承项目级约束和跨平台要求

## 11. 后续版本边界

以下内容明确留给后续版本：

- Prompt 模板自动拼装
- 模型路由
- Git checkpoint
- 测试状态收集
- 多任务依赖关系
- 会话摘要与上下文压缩
- 执行阶段状态机

第一版不提前承载这些职责。

## 12. 结论

第一版 `SOP 执行器` 的核心，不是“自动完成任务”，而是：

> 把一句自然语言需求，转换为一个带状态、带边界、带约束、待人工确认的任务契约。

只要这一步足够稳定，后续执行、调度、压缩、路由等能力才有可靠基础。
