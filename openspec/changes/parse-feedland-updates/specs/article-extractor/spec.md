## ADDED Requirements

### Requirement: 提取文章主要内容
系统必须使用 Newspaper3k 库提取每篇文章的主要内容。

#### Scenario: 从标准文章提取内容
- **WHEN** 文章具有清晰的主要内容结构
- **THEN** 系统提取文章标题、正文和发布日期

#### Scenario: 使用 BeautifulSoup 回退提取内容
- **WHEN** Newspaper3k 无法提取内容
- **THEN** 系统使用 BeautifulSoup 解析和提取内容

#### Scenario: 文章在付费墙后面
- **WHEN** 文章在付费墙后面或需要登录
- **THEN** 系统提取可用内容或标记为不可访问

### Requirement: 提取文章元数据
系统必须提取文章元数据，包括标题、URL、发布日期和作者。

#### Scenario: 提取完整元数据
- **WHEN** 文章具有所有元数据字段
- **THEN** 系统提取标题、URL、发布日期和作者

#### Scenario: 缺少发布日期
- **WHEN** 文章没有发布日期
- **THEN** 系统使用当前日期或 feed 日期作为备用

#### Scenario: 缺少作者
- **WHEN** 文章没有作者信息
- **THEN** 系统将作者设置为"Unknown"或从 feed 中提取

### Requirement: 处理内容提取失败
系统必须优雅地处理内容提取失败并继续处理。

#### Scenario: 无效的文章 URL
- **WHEN** 文章 URL 无效或无法访问
- **THEN** 系统记录错误并将文章标记为失败

#### Scenario: HTML 解析错误
- **WHEN** 无法解析文章 HTML
- **THEN** 系统记录错误并将文章标记为失败

#### Scenario: 空的文章内容
- **WHEN** 提取的内容为空或太短
- **THEN** 系统记录警告并将文章标记为低质量

### Requirement: 域名黑名单管理
系统必须记录解析失败的域名，并在后续处理中跳过这些域名的文章。

#### Scenario: 首次解析失败时记录域名
- **WHEN** 文章解析失败（Newspaper3k 和 BeautifulSoup 都失败）
- **THEN** 系统将文章 URL 的域名添加到黑名单

#### Scenario: 跳过黑名单域名的文章
- **WHEN** 文章 URL 的域名在黑名单中
- **THEN** 系统跳过该文章的解析，不进行网络请求

#### Scenario: 持久化黑名单到配置文件
- **WHEN** 黑名单被更新
- **THEN** 系统将黑名单保存到 config.json 的 `blacklist` 字段

#### Scenario: 从配置文件加载黑名单
- **WHEN** 系统启动时
- **THEN** 系统从 config.json 的 `blacklist` 字段加载已保存的黑名单