## ADDED Requirements

### Requirement: 解析 Feedland OPML URL
系统必须从 config.json 的 `url` 字段读取 Feedland OPML URL，并解析 OPML 文档以提取所有 feed 订阅。

#### Scenario: 成功解析 OPML
- **WHEN** config.json 包含有效的 Feedland OPML URL（例如 `https://feedland.com/opml?screenname=yonglelaoren`）
- **THEN** 系统解析 OPML 文档并提取所有 feed URL 及其元数据（标题、类型）

#### Scenario: 无效的 OPML URL
- **WHEN** config.json 中的 OPML URL 无效或无法访问
- **THEN** 系统返回适当的错误消息，指示 URL 无效

#### Scenario: 空的 OPML 响应
- **WHEN** OPML URL 返回空文档或没有 feeds
- **THEN** 系统返回空的 feed 列表并附带适当的状态

#### Scenario: 配置文件缺少 URL
- **WHEN** config.json 中缺少 `url` 字段
- **THEN** 系统返回错误消息，指示配置不完整

### Requirement: 提取 feed 元数据
系统必须从 OPML 文档中提取 feed 元数据，包括标题、URL 和 feed 类型。

#### Scenario: 提取 RSS feed 元数据
- **WHEN** OPML 包含 RSS feed 条目
- **THEN** 系统提取 feed 标题、URL，并将其识别为 RSS 类型

#### Scenario: 提取 Atom feed 元数据
- **WHEN** OPML 包含 Atom feed 条目
- **THEN** 系统提取 feed 标题、URL，并将其识别为 Atom 类型

#### Scenario: 缺少 feed 标题
- **WHEN** OPML feed 条目没有标题属性
- **THEN** 系统使用 feed URL 作为备用标题