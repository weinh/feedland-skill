## ADDED Requirements

### Requirement: 跟踪每个 feed 的最后提取时间
系统必须使用 `{url: time}` 结构记录从每个 feed 提取的最新文章的时间戳，并存储到 config.json 的 `his` 字段。

#### Scenario: 记录首次提取
- **WHEN** 首次从 feed 提取文章
- **THEN** 系统记录该 feed URL 最新文章的时间戳到 config.json 的 `his` 字段

#### Scenario: 更新现有 feed 时间戳
- **WHEN** 提取文章并发现更新的文章
- **THEN** 系统更新 config.json 中该 feed URL 的时间戳

#### Scenario: 没有新文章
- **WHEN** 没有发现新文章（所有文章都比记录的时间戳更旧）
- **THEN** 系统保持 config.json 中现有时间戳不变

### Requirement: 存储 feed 跟踪数据
系统必须将 feed 跟踪数据持久化到 config.json 的 `his` 字段以供将来参考。

#### Scenario: 保存 feed 跟踪数据
- **WHEN** feed 提取完成
- **THEN** 系统将 `{url: time}` 映射保存到 config.json 的 `his` 字段

#### Scenario: 加载 feed 跟踪数据
- **WHEN** 系统开始 feed 提取
- **THEN** 系统从 config.json 的 `his` 字段加载现有的 `{url: time}` 映射

#### Scenario: 处理缺少 his 字段
- **WHEN** config.json 中缺少 `his` 字段
- **THEN** 系统初始化为空的跟踪数据对象

### Requirement: 使用时间戳进行增量提取
系统必须使用记录的时间戳仅从每个 feed 提取新文章。

#### Scenario: 仅提取新文章
- **WHEN** 使用现有时间戳记录处理 feed
- **THEN** 系统仅提取时间戳比记录时间更新的文章

#### Scenario: 首次 feed 提取
- **WHEN** feed 没有先前的时间戳记录
- **THEN** 系统无论时间戳如何都提取 5 篇最新文章

#### Scenario: 时间戳比较以进行过滤
- **WHEN** 比较文章时间戳
- **THEN** 系统与 feed 的记录时间戳进行比较，而不是与整体最新时间比较