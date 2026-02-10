# Feedland Skill - OpenSpec 项目

## 项目概述

Feedland Skill 是一个基于 OpenSpec 规范驱动的开发工具集，提供了完整的变更管理工作流。该项目通过结构化的文档驱动开发流程，帮助团队更有效地管理功能开发、问题修复和技术变更。

### 核心技术

- **OpenSpec CLI**: 规范驱动的变更管理系统
- **iFlow CLI**: 智能命令行代理框架
- **Markdown**: 所有规范和文档的标准格式
- **Schema 驱动**: 支持多种工作流模式（默认为 spec-driven）

### 项目架构

项目采用分层架构：

```
feedland-skill/
├── .iflow/                    # iFlow 配置和技能
│   ├── commands/              # 自定义命令定义
│   │   ├── opsx-new.md        # 创建新变更
│   │   ├── opsx-continue.md   # 继续变更
│   │   ├── opsx-apply.md      # 应用变更（实现任务）
│   │   ├── opsx-verify.md     # 验证变更
│   │   ├── opsx-archive.md    # 归档变更
│   │   ├── opsx-bulk-archive.md  # 批量归档
│   │   ├── opsx-ff.md         # 快速前进到任务
│   │   ├── opsx-sync.md       # 同步规范
│   │   ├── opsx-explore.md    # 探索模式
│   │   └── opsx-onboard.md    # 入门指导
│   └── skills/                # 技能实现
│       ├── openspec-new-change/
│       ├── openspec-continue-change/
│       ├── openspec-apply-change/
│       ├── openspec-verify-change/
│       ├── openspec-archive-change/
│       ├── openspec-bulk-archive-change/
│       ├── openspec-ff-change/
│       ├── openspec-sync-specs/
│       ├── openspec-explore/
│       └── openspec-onboard/
├── openspec/                  # OpenSpec 规范存储
│   ├── config.yaml            # 项目配置
│   ├── changes/               # 活跃变更
│   │   └── archive/           # 已归档变更
│   └── specs/                 # 主规范
└── AGENTS.md                  # AI 代理上下文文件
```

## 构建和运行

### 前置要求

- Python 3.9+
- OpenSpec CLI（必须安装）
- iFlow CLI

### 可用命令

项目提供以下自定义命令（通过 `/opsx:<command>` 访问）：

#### 变更管理命令

- `/opsx:new <name>` - 创建新的变更
- `/opsx:continue` - 继续当前变更，创建下一个文档
- `/opsx:apply <name>` - 实现变更中的任务
- `/opsx:verify <name>` - 验证实现是否符合规范
- `/opsx:archive <name>` - 归档完成的变更
- `/opsx:bulk-archive` - 批量归档多个变更
- `/opsx:ff <name>` - 快速前进到任务阶段

#### 规范管理命令

- `/opsx:sync <name>` - 将增量规范同步到主规范

#### 探索和入门命令

- `/opsx:explore` - 进入探索模式，思考和研究
- `/opsx:onboard` - 项目入门指导

### 核心工作流

#### 1. Spec-Driven 工作流（默认）

这是标准的工作流程，按以下顺序创建文档：

```
proposal.md → specs/ → design.md → tasks.md → 实现 → 验证 → 归档
```

**步骤说明：**

1. **创建变更**: `/opsx:new <change-name>`
   - 创建变更目录
   - 显示第一个文档（proposal）的模板

2. **编写提案**: 使用 `/opsx:continue`
   - 描述变更的目的、范围和影响
   - 列出涉及的能力（capabilities）

3. **编写规范**: 使用 `/opsx:continue`
   - 为每个能力创建详细的规范文档
   - 包含需求（requirements）和场景（scenarios）

4. **设计**: 使用 `/opsx:continue`
   - 记录技术决策和架构
   - 说明实现方法

5. **任务分解**: 使用 `/opsx:continue`
   - 将实现分解为可检查的任务列表

6. **实现**: 使用 `/opsx:apply`
   - 按任务列表实现代码
   - 逐个完成任务并标记

7. **验证**: 使用 `/opsx:verify`
   - 验证实现是否符合规范
   - 检查完整性、正确性和一致性

8. **同步规范**（可选）: `/opsx:sync`
   - 将增量规范更新到主规范
   - 保持主规范与变更同步

9. **归档**: 使用 `/opsx:archive`
   - 完成变更后归档
   - 将变更移至 archive 目录

#### 2. 探索模式

使用 `/opsx:explore` 进入探索模式：

- **用途**: 在创建变更前进行思考和研究
- **特点**: 可以读取文件、搜索代码库，但不实现功能
- **何时使用**: 需要澄清需求、探索问题空间、比较方案时

#### 3. 快速前进模式

使用 `/opsx:ff <name>` 快速前进到任务阶段：

- **用途**: 跳过文档创建，直接进入实现
- **何时使用**: 变更简单明确，不需要详细文档

### 常用 OpenSpec CLI 命令

```bash
# 查看所有变更
openspec list --json

# 查看变更状态
openspec status --change <name>

# 获取文档指令
openspec instructions <artifact-id> --change <name>

# 获取应用指令
openspec instructions apply --change <name> --json

# 查看可用的工作流
openspec schemas --json
```

## 开发约定

### 命名约定

- **变更名称**: 使用 kebab-case（小写，用连字符分隔），例如 `add-user-auth`
- **能力名称**: 使用描述性名称，反映具体功能
- **文档命名**: 遵循 OpenSpec 标准命名

### 文档结构

#### Proposal (proposal.md)

```markdown
## Why
解释为什么需要这个变更

## What Changes
描述将要改变的内容

## Capabilities
列出所有涉及的能力

## Impact
说明变更的影响范围
```

#### Spec (specs/<capability>/spec.md)

```markdown
## Purpose
说明这个能力的目的

## Requirements
### Requirement: <名称>
需求描述

#### Scenario: <场景>
- **WHEN** 条件
- **THEN** 期望结果
```

#### Design (design.md)

```markdown
## Overview
总体设计概述

## Architecture
架构说明

## Implementation Approach
实现方法

## Key Decisions
关键决策及其理由
```

#### Tasks (tasks.md)

```markdown
## Implementation Tasks
- [ ] 任务 1
- [ ] 任务 2
- [ ] 任务 3
```

### 增量规范格式

当需要修改现有规范时，使用增量规范格式：

```markdown
## ADDED Requirements
新增的需求

## MODIFIED Requirements
修改的需求（只包含变化部分）

## REMOVED Requirements
移除的需求

## RENAMED Requirements
- FROM: `### Requirement: 旧名称`
- TO: `### Requirement: 新名称`
```

### 代码约定

1. **最小化更改**: 每个任务应保持最小范围
2. **立即标记**: 完成任务后立即在 tasks.md 中标记为完成 `- [x]`
3. **保持一致**: 遵循项目现有的代码模式和风格
4. **智能合并**: 同步规范时，只应用变更部分，保留其他内容

### 验证标准

变更必须通过以下验证才能归档：

**完整性（Completeness）**:
- 所有任务已完成
- 所有需求已实现

**正确性（Correctness）**:
- 实现符合规范意图
- 所有场景都已覆盖

**一致性（Coherence）**:
- 遵循设计决策
- 代码模式一致

## 配置文件

### openspec/config.yaml

```yaml
schema: spec-driven

# 项目上下文（可选）
# 向 AI 展示技术栈、约定、风格指南等
context: |
  Tech stack: [项目技术栈]
  We use conventional commits
  Domain: [领域描述]

# 每个文档的规则（可选）
rules:
  proposal:
    - 保持提案简洁
    - 始终包含影响分析
  tasks:
    - 将任务分解为 2 小时内的块
```

## 工作模式

### 流式工作（Fluid Workflow）

OpenSpec 支持灵活的工作流程，不强制严格的阶段划分：

- **可以随时开始实现**: 即使文档未完全完成，如果有任务就可以开始实现
- **允许文档更新**: 实现过程中发现设计问题可以更新文档
- **支持交叉进行**: 可以在实现和文档创建之间交替进行

### 探索模式（Explore Mode）

探索模式是一个独立的思考阶段：

- **不是工作流**: 没有固定步骤，不需要特定输出
- **不是实现**: 可以读取和调查，但不编写代码
- **可以创建文档**: 如果需要可以创建 OpenSpec 文档来记录思考
- **何时使用**: 需要澄清需求、探索问题、比较方案时

## 关键概念

### Schema（工作流模式）

定义文档创建的顺序和依赖关系。项目默认使用 `spec-driven` schema，但可以配置其他模式。

### Artifact（文档）

OpenSpec 中的文档称为 artifact，包括：
- proposal: 提案
- specs: 规范
- design: 设计
- tasks: 任务
- 其他自定义文档

### Change（变更）

一个变更包含一组相关的文档，代表一个功能、修复或改进。

### Delta Spec（增量规范）

在变更目录中的规范称为增量规范，包含对主规范的修改（ADDED/MODIFIED/REMOVED/RENAMED）。

## 使用技巧

### 1. 开始新变更

```bash
/opsx:new add-feature-name
```

然后描述你想构建什么，AI 会引导你完成第一个文档。

### 2. 继续工作

```bash
/opsx:continue
```

AI 会创建下一个文档并显示模板。

### 3. 实现任务

```bash
/opsx:apply
```

AI 会读取上下文并开始实现任务列表。

### 4. 快速前进

```bash
/opsx:ff simple-fix
```

跳过文档创建，直接进入实现阶段。

### 5. 验证实现

```bash
/opsx:verify
```

AI 会验证实现是否符合规范，并提供详细的报告。

### 6. 同步规范

```bash
/opsx:sync
```

将变更中的增量规范更新到主规范，智能合并变更。

### 7. 归档变更

```bash
/opsx:archive
```

完成变更后归档，将变更移至历史记录。

## 故障排除

### 变更名称无效

确保使用 kebab-case（小写，连字符分隔）：
- ✅ `add-user-auth`
- ❌ `AddUserAuth`
- ❌ `add_user_auth`

### 文档被阻塞

如果文档显示为 "blocked"，说明依赖的文档还未完成。继续创建前置文档。

### 任务不明确

如果任务描述不清楚，使用 `/opsx:explore` 进入探索模式，先澄清需求。

### 实现与规范不符

使用 `/opsx:verify` 检查实现是否符合规范，根据报告进行修正。

## 扩展和自定义

### 添加新的 Schema

在 OpenSpec 配置中定义新的工作流模式。

### 添加自定义规则

在 `config.yaml` 的 `rules` 部分添加特定文档的规则。

### 扩展技能

在 `.iflow/skills/` 目录中添加新的技能实现。

## 项目特定信息

### 当前配置

- **Schema**: spec-driven
- **上下文**: 未配置（可在 config.yaml 中添加）
- **自定义规则**: 未配置

### 活跃变更

使用 `openspec list --json` 查看当前活跃的变更。

### 已归档变更

已归档的变更位于 `openspec/changes/archive/` 目录。

## 最佳实践

1. **从探索开始**: 对于复杂变更，先使用 `/opsx:explore` 澄清需求
2. **保持文档更新**: 实现过程中发现问题时及时更新文档
3. **小步快跑**: 将任务分解为小的、可完成的单元
4. **频繁验证**: 实现过程中定期使用 `/opsx:verify` 检查进度
5. **及时归档**: 完成后及时归档，保持工作区清洁
6. **同步规范**: 完成后使用 `/opsx:sync` 更新主规范

## 参考资源

- OpenSpec CLI 文档
- iFlow CLI 文档
- 项目内部的技能实现文件（`.iflow/skills/`）
- 项目内部的命令定义文件（`.iflow/commands/`）