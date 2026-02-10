## Why

Feedland 提供了一个包含多个 RSS/Atom 源的 OPML 接口，需要从这些源中提取最新文章内容。当前缺少一个统一的解析器来处理混合格式的 feeds，并且需要避免重复处理已提取的文章，以提高效率并减少不必要的网络请求。

## What Changes

- 新增从 Feedland OPML URL 解析和提取 RSS/Atom feeds 的功能（URL 从 config.json 的 `url` 字段读取）
- 每个订阅源最多只解析最新的 5 篇文章
- 记录每个订阅源最后一篇文章的更新或发布时间，使用 `{url: time}` 结构存储到 config.json 的 `his` 字段
- 使用 Newspaper3k 提取文章主要内容，使用 BeautifulSoup 处理自定义解析需求
- 实现基于 URL 和时间戳的去重机制，避免重复提取
- 将提取的内容以结构化格式（JSON）存储

## Capabilities

### New Capabilities

- `feedland-opml-parser`: 解析 Feedland OPML 接口，提取所有订阅源 URL 和元数据
- `mixed-feed-parser`: 处理混合格式的 RSS/Atom feeds，支持多种 feed 格式
- `article-extractor`: 使用 Newspaper3k 和 BeautifulSoup 提取文章主要内容
- `article-deduplication`: 基于 URL 和时间戳的去重机制，跟踪已处理文章
- `feed-tracker`: 使用 `{url: time}` 结构记录每个订阅源的最后提取时间

### Modified Capabilities

（无现有能力需要修改）

## Impact

**新增依赖**:
- Newspaper3k（文章内容提取）
- BeautifulSoup4（HTML 解析）
- Feedparser（RSS/Atom 解析）
- Requests（HTTP 请求）

**受影响的代码**:
- 新增 Feedland 解析模块
- 新增文章提取和去重模块
- 新增时间戳跟踪机制
- 命令行接口（CLI）

**发布和部署**:
- 支持 PyPI 包发布，可通过 pip 安装
- 支持打包为独立可执行文件（使用 PyInstaller）
- 支持 Docker 容器化部署
- 配置文件支持多路径查找

**数据存储**:
- 使用 config.json 配置文件存储：
  - `url`: Feedland OPML URL
  - `threads`: 并行处理的线程数（可选，未配置时使用合理默认值）
  - `his`: 每个订阅源的最后提取时间映射 `{url: time}`

**性能影响**:
- 每次解析最多获取每个源的 5 篇最新文章，减少网络负载
- 基于时间戳的去重避免重复处理，提高效率

**边界情况**:
- 处理 RSS、Atom 混合格式
- 处理 feed 解析失败、网络错误
- 处理缺少更新时间戳的 feeds