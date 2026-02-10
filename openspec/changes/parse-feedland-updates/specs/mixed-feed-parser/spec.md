## ADDED Requirements

### Requirement: 解析混合 RSS/Atom feeds
系统必须使用 feedparser 库解析 feed，无论其格式如何（RSS 或 Atom）。

#### Scenario: 解析 RSS 2.0 feed
- **WHEN** feed URL 提供 RSS 2.0 feed
- **THEN** 系统成功解析所有 feed 条目

#### Scenario: 解析 Atom feed
- **WHEN** feed URL 提供 Atom feed
- **THEN** 系统成功解析所有 feed 条目

#### Scenario: 解析 RSS 1.0 feed
- **WHEN** feed URL 提供 RSS 1.0 feed
- **THEN** 系统成功解析所有 feed 条目

### Requirement: 限制每个 feed 的文章数量
系统必须从每个 feed 中最多提取 5 篇最新文章。

#### Scenario: Feed 包含超过 5 篇文章
- **WHEN** feed 包含超过 5 篇文章
- **THEN** 系统仅提取根据发布/更新时间确定的 5 篇最新文章

#### Scenario: Feed 恰好包含 5 篇文章
- **WHEN** feed 恰好包含 5 篇文章
- **THEN** 系统提取所有 5 篇文章

#### Scenario: Feed 包含少于 5 篇文章
- **WHEN** feed 包含少于 5 篇文章
- **THEN** 系统提取所有可用的文章

### Requirement: 处理 feed 解析错误
系统必须优雅地处理 feed 解析失败并继续处理其他 feeds。

#### Scenario: Feed 无法访问
- **WHEN** feed URL 返回网络错误或超时
- **THEN** 系统记录错误并继续处理下一个 feed

#### Scenario: Feed 格式无效
- **WHEN** feed 包含格式错误的 XML 或无效格式
- **THEN** 系统记录错误并继续处理下一个 feed

#### Scenario: Feed 返回 HTTP 错误
- **WHEN** feed URL 返回 4xx 或 5xx HTTP 状态
- **THEN** 系统记录错误并继续处理下一个 feed