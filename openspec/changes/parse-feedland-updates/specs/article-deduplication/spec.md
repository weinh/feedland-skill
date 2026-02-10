## ADDED Requirements

### Requirement: 通过 URL 和时间戳对文章去重
系统必须使用文章 URL 和发布时间戳来识别和跳过重复文章。

#### Scenario: 文章已处理
- **WHEN** 文章 URL 和时间戳与之前处理的文章匹配
- **THEN** 系统跳过提取并标记为重复

#### Scenario: 相同 URL 但不同时间戳的新文章
- **WHEN** 文章 URL 存在但时间戳更新
- **THEN** 系统将其视为新文章并处理

#### Scenario: 不同 URL 的新文章
- **WHEN** 文章 URL 不在处理历史记录中
- **THEN** 系统将该文章作为新文章处理

### Requirement: 跟踪已处理的文章
系统必须维护已处理文章的记录以避免重复处理。

#### Scenario: 记录新文章
- **WHEN** 文章成功处理
- **THEN** 系统将文章 URL 和时间戳添加到处理记录中

#### Scenario: 加载已处理文章历史
- **WHEN** 系统开始处理
- **THEN** 系统从存储中加载现有的已处理文章记录

#### Scenario: 持久化已处理文章记录
- **WHEN** 处理完成
- **THEN** 系统将已处理文章记录保存到存储

### Requirement: 处理去重边界情况
系统必须处理去重逻辑中的边界情况。

#### Scenario: 文章缺少时间戳
- **WHEN** 文章没有发布时间戳
- **THEN** 系统使用 feed 时间戳或当前时间进行去重

#### Scenario: 文章 URL 包含查询参数
- **WHEN** 文章 URL 有变化的查询参数
- **THEN** 系统标准化 URL（移除跟踪参数）以进行去重

#### Scenario: 重复检测失败
- **WHEN** 由于存储错误导致重复检查失败
- **THEN** 系统记录警告并继续处理（可能会处理重复项）