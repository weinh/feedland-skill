## Context

当前系统缺乏从 Feedland OPML 接口统一解析 RSS/Atom feeds 的能力。用户需要从多个订阅源提取最新文章内容，但现有的解决方案不支持混合格式的 feeds，也没有有效的去重机制来避免重复处理相同文章。

**当前状态**：
- 没有统一的 feed 解析器
- 没有去重机制
- 没有增量提取能力

**约束条件**：
- 技术栈：Python 3.11+、BeautifulSoup4、Newspaper3k、Feedparser
- 必须处理 RSS 和 Atom 混合格式
- 使用 config.json 存储配置和历史记录
- 每个 feed 最多提取 5 篇最新文章
- 必须避免重复提取已处理的文章

**相关方**：
- 需要从多个订阅源提取文章内容的用户
- Feedland API 使用者

## Goals / Non-Goals

**Goals:**
- 提供统一的 Feedland OPML 解析能力，支持 RSS 和 Atom 混合格式
- 实现基于时间戳的去重机制，避免重复提取
- 支持增量提取，仅处理新文章
- 提供灵活的文章内容提取，使用 Newspaper3k 和 BeautifulSoup

**Non-Goals:**
- 不提供 feed 订阅管理功能
- 不提供文章内容的存储和检索功能
- 不支持实时推送通知
- 不提供文章内容的翻译或摘要功能

## Decisions

### 1. 使用 feedparser 作为主要 feed 解析库

**决策**：使用 feedparser 库解析 RSS/Atom feeds

**理由**：
- feedparser 是成熟的 Python 库，支持多种 feed 格式（RSS 0.9x, 1.0, 2.0, Atom）
- 自动处理不同格式的差异，简化代码
- 活跃维护，社区支持良好

**替代方案**：
- 使用 xml.etree.ElementTree 手动解析 → 需要处理多种格式差异，代码复杂度高
- 使用 feedgen → 适用于生成 feed，不适用于解析

### 2. 双层内容提取策略

**决策**：优先使用 Newspaper3k 提取内容，失败时回退到 BeautifulSoup

**理由**：
- Newspaper3k 专门为新闻文章设计，能准确提取主要内容
- BeautifulSoup 提供更底层的 HTML 解析能力，可以作为后备方案
- 双层策略提高提取成功率

**实现细节**：
- 首先尝试使用 Newspaper3k 的 `Article` 类提取
- 如果 Newspaper3k 提取失败或内容为空，使用 BeautifulSoup 解析
- BeautifulSoup 策略：查找常见的文章容器（如 `<article>`、`<main>` 或具有特定 class 的 div）

### 3. 基于 Feed 级别的时间戳去重

**决策**：使用 `{feed_url: timestamp}` 结构记录每个 feed 的最后提取时间，存储在 config.json 的 `his` 字段

**理由**：
- 相比基于文章 URL 的去重，Feed 级别更简单高效
- 每个 feed 只需存储一个时间戳，数据量小
- 符合"每次提取最多 5 篇最新文章"的需求

**替代方案**：
- 基于文章 URL 的去重 → 需要存储所有已处理文章 URL，随着时间增长数据量变大
- 基于内容哈希的去重 → 计算开销大，可能误判相似文章为重复

**实现细节**：
- 首次提取 feed 时，提取 5 篇最新文章并记录最新文章的时间戳
- 后续提取时，只提取时间戳比记录时间更新的文章
- 如果没有新文章，保持原有时间戳不变

### 4. 配置驱动设计

**决策**：使用 config.json 存储 OPML URL 和历史记录

**理由**：
- 集中配置管理，易于修改
- JSON 格式易于读写和版本控制
- 支持手动编辑配置文件

**配置结构**：
```json
{
  "url": "https://feedland.com/opml?screenname=yonglelaoren",
  "his": {
    "https://example.com/feed.xml": "2025-02-09T10:00:00Z",
    "https://example.org/atom": "2025-02-09T11:30:00Z"
  }
}
```

### 5. 容错性设计

**决策**：单个 feed 解析失败不影响其他 feeds 的处理

**理由**：
- 部分订阅源可能暂时不可用或格式错误
- 不应因为一个 feed 失败而停止整个提取过程

**实现细节**：
- 使用 try-except 捕获每个 feed 的解析异常
- 记录失败信息但继续处理下一个 feed
- 返回包含成功和失败信息的完整报告

### 6. 并行处理设计

**决策**：使用 `concurrent.futures.ThreadPoolExecutor` 并行处理多个 feeds，线程数从 config.json 的 `threads` 字段读取

**理由**：
- I/O 密集型任务（网络请求）适合多线程并行处理
- Python 标准库，无需额外依赖
- 线程数可配置，适应不同环境和需求
- 代码简洁，易于维护

**实现细节**：
- 从 config.json 的 `threads` 字段读取并发数
- 如果未配置或配置无效，使用默认值 `min(10, cpu_count() * 2 + 1)`
- 使用 `ThreadPoolExecutor` 创建线程池
- 每个 feed 的解析和文章提取在一个独立线程中执行
- 使用 `concurrent.futures.as_completed` 收集结果
- 确保线程安全：config.json 的读写使用文件锁

**配置示例**：
```json
{
  "url": "https://feedland.com/opml?screenname=yonglelaoren",
  "threads": 10,
  "his": {
    "https://example.com/feed.xml": "2025-02-09T10:00:00Z"
  }
}
```

**替代方案**：
- asyncio → 异步 I/O，但需要大量代码重构
- multiprocessing → 进程间通信开销大，不适合 I/O 密集型任务

### 7. 域名黑名单机制

**决策**：使用运行时黑名单，避免重复解析失败的域名

**理由**：
- 提高效率：避免重复尝试已知失败的 URL
- 减少网络负载：失败域名不再重复请求
- 灵活性：运行时黑名单，每次启动都是空的，适应网站临时问题

**实现细节**：
- 使用 `DomainBlacklist` 类管理黑名单
- 使用 `threading.Lock` 实现线程安全操作
- 添加条件：URL 提取失败就添加黑名单（不管有没有描述内容）
- 黑名单检查：在黑名单中的域名直接使用描述内容，不再尝试提取 URL
- 不持久化：程序退出后自动清空，不保存到配置文件

**工作流程**：
```
1. 检查域名是否在黑名单中
   - 在黑名单中 → 直接使用描述内容（如果有）
   - 不在黑名单中 → 继续

2. 尝试提取 URL 内容
   - 成功 → 返回内容
   - 失败 → 添加到黑名单 → 尝试描述内容

3. 描述内容回退
   - 有描述（≥50 字符）→ 使用描述 → 返回成功
   - 无描述或太短 → 返回失败
```

### 8. 三层内容提取策略

**决策**：cloudscraper → newspaper3k → beautifulsoup → 描述内容

**理由**：
- cloudscraper：可绕过 Cloudflare 保护，提高成功率
- newspaper3k：专为新闻文章设计，准确提取主要内容
- beautifulsoup：提供底层 HTML 解析能力，作为最后回退
- 描述内容：即使 URL 失败，也能获取 feed 中的有用信息

**实现细节**：
- 优先使用 cloudscraper（如果可用）
- 失败后使用 newspaper3k
- 再次失败后使用 beautifulsoup
- 最后使用 feed 中的描述内容
- 每层都进行内容验证，确保质量

### 9. 内容验证机制

**决策**：对所有提取的内容进行验证，拒绝乱码内容

**理由**：
- 确保输出质量：不返回无法阅读的内容
- 防止编码问题：检测和处理各种编码错误
- 自动化质量控制：减少人工审核需求

**验证标准**：
- 长度检查：内容必须至少 50 字符
- 控制字符检查：不可打印字符比例 ≤ 10%
- Null 字符检查：不允许包含任何 null 字符
- 编码验证：确保内容是有效的 UTF-8 编码

**实现细节**：
- 实现 `_is_content_valid()` 方法
- 在每次提取成功后验证内容
- 验证失败继续尝试下一个提取方法
- 记录验证失败的日志

### 10. 描述内容回退机制

**决策**：当 URL 提取失败时，使用 feed 中的描述内容作为回退

**理由**：
- 提高成功率：即使 URL 失败，也能获取有用信息
- 减少失败率：很多 feed 都包含摘要或描述
- 用户体验：即使无法获取完整内容，也能看到摘要

**实现细节**：
- 从 feed 条目提取 description、summary 或 content 字段
- 支持多种字段格式（字符串、字典、列表）
- 验证描述内容（≥50 字符，无乱码）
- 将描述内容传递给 ArticleExtractor

**字段优先级**：
1. `description` - 标准描述字段
2. `summary` - Atom 格式的摘要
3. `content` - 完整内容字段（可能是 HTML）

### 11. 历史时间过滤

**决策**：不处理发布时间不晚于历史时间的文章

**理由**：
- 提高效率：避免处理已知已处理的文章
- 节省资源：减少不必要的网络请求和解析
- 符合增量提取需求

**实现细节**：
- 在处理每篇文章前检查发布时间
- 如果有历史时间且文章时间不新于历史时间，停止处理
- 使用 datetime 进行时间比较
- 处理各种时间格式和时区问题

## Risks / Trade-offs

### Risk 1: 时间戳格式不一致
**风险**：不同 feeds 的时间戳格式可能不同（RFC 3339、ISO 8601、自定义格式）

**缓解措施**：
- 使用 dateutil.parser 解析时间戳，支持多种格式
- 如果解析失败，使用当前时间作为备用
- 在文档中说明时间戳要求

### Risk 2: Newspaper3k 提取失败率高
**风险**：某些网站的结构可能不适合 Newspaper3k，导致提取失败

**缓解措施**：
- 实现 BeautifulSoup 回退机制
- 记录提取失败的 feed URL，便于后续优化
- 考虑支持自定义提取规则

### Risk 3: 网络请求超时或限流
**风险**：大量 feed 请求可能导致超时或被服务器限流

**缓解措施**：
- 设置合理的超时时间（例如 10 秒）
- 添加请求重试机制（最多 3 次）
- 考虑实现请求间隔，避免短时间内大量请求

### Risk 4: 配置文件并发写入冲突
**风险**：多个进程同时更新 config.json 可能导致数据冲突

**缓解措施**：
- 使用文件锁机制防止并发写入
- 暂时假设单进程运行，未来如需并发再考虑分布式锁

### Risk 5: 域名黑名单误判
**风险**：某些网站暂时不可用，可能被错误地加入黑名单

**缓解措施**：
- 使用运行时黑名单，每次启动都是空的
- 在黑名单中仍可使用描述内容，不影响结果
- 提供手动清除黑名单的方法（如重启程序）

### Risk 6: 内容验证误判
**风险**：某些特殊格式的内容可能被误判为乱码

**缓解措施**：
- 使用保守的验证标准（10% 控制字符阈值）
- 记录验证失败的日志，便于调试
- 提供手动验证的选项

### Risk 7: 描述内容质量不稳定
**风险**：不同 feed 的描述内容质量差异很大

**缓解措施**：
- 设置最小长度要求（50 字符）
- 进行内容验证，确保无乱码
- 优先使用 URL 提取的内容，描述仅作为回退

### Trade-off 1: Feed 级别 vs 文章级别去重
**权衡**：Feed 级别去重简单高效，但可能在某些情况下重复提取（例如文章被重新发布但 URL 不变）

**选择**：选择 Feed 级别去重，因为：
- 实现简单，维护成本低
- 数据存储需求小
- 对于大多数使用场景足够准确
- 可以在未来根据需要升级为文章级别去重

### Trade-off 2: 固定 5 篇文章限制
**权衡**：固定限制简化实现，但可能不适合所有场景（某些用户可能需要更多或更少的文章）

**选择**：选择固定 5 篇限制，因为：
- 符合当前需求
- 简化设计和实现
- 可以在未来添加配置项允许用户自定义

### Trade-off 3: 运行时黑名单 vs 持久化黑名单
**权衡**：运行时黑名单每次启动都是空的，持久化黑名单可以记住历史失败

**选择**：选择运行时黑名单，因为：
- 网站问题可能是临时的，下次启动时可能已经修复
- 避免永久阻止某个域名
- 提高灵活性，适应网站变化

### Trade-off 4: URL 提取失败就添加黑名单
**权衡**：即使有描述内容，URL 失败也会添加黑名单，可能导致某些网站完全被跳过

**选择**：选择 URL 失败就添加黑名单，因为：
- 在黑名单中会直接使用描述内容，不影响结果
- 避免重复失败的请求，提高效率
- 描述内容提供了备选方案

### Trade-off 5: 内容验证严格度
**权衡**：严格的内容验证可能拒绝一些边缘情况的有效内容

**选择**：选择适中的验证标准（10% 控制字符阈值），因为：
- 平衡了质量和覆盖率
- 大多数乱码都能被检测到
- 极少数边缘情况可能被误判，但影响较小

## Architecture

### 模块划分

```
yonglelaoren-feedland-parser/
├── src/
│   └── yonglelaoren_feedland_parser/    # Python 包名
│       ├── __init__.py
│       ├── config.py           # 配置文件读写
│       ├── opml_parser.py      # OPML 解析
│       ├── feed_parser.py      # Feed 解析和文章提取
│       ├── article_extractor.py # 文章内容提取（多层回退策略）
│       ├── domain_blacklist.py # 域名黑名单管理（线程安全）
│       ├── deduplicator.py     # 去重逻辑
│       └── tracker.py          # 时间戳跟踪
├── pyproject.toml          # 项目配置和依赖管理
├── config.json             # 配置文件示例
├── cli.py                  # 命令行入口
└── README.md               # 项目文档
```

### 数据流

```
config.json
    │
    ├── 读取 OPML URL
    │
    ▼
OPML Parser
    │
    ├── 解析 OPML
    │
    ▼
Feed URLs + Metadata
    │
    ├── 使用 ThreadPoolExecutor 并行处理每个 feed
    │
    ▼
Feed Parser (并行执行)
    │
    ├── 使用 feedparser 解析 feed
    ├── 获取历史时间（从 tracker）
    │
    ▼
Articles (按顺序处理)
    │
    ├── 检查域名黑名单
    │   ├── 在黑名单中？
    │   │   ├── 有描述内容 → 使用描述内容（成功）
    │   │   └── 无描述内容 → 跳过（失败）
    │   └── 不在黑名单中 → 继续
    │
    ├── 检查发布时间
    │   └── 不晚于历史时间？ → 停止处理
    │
    ├── 提取 URL 内容
    │   ├── 尝试 cloudscraper
    │   │   └── 失败？ → 尝试 newspaper3k
    │   ├── 尝试 newspaper3k
    │   │   └── 失败？ → 尝试 beautifulsoup
    │   └── 尝试 beautifulsoup
    │       └── 失败？ → 使用描述内容
    │
    ├── 验证内容质量
    │   ├── 检查长度（≥100 字符）
    │   ├── 检查控制字符比例（≤10%）
    │   ├── 检查 null 字符（0 个）
    │   └── 检查编码有效性
    │   ├── 验证失败？ → 尝试下一个方法
    │   └── 验证成功？ → 继续
    │
    ├── 处理提取结果
    │   ├── 成功 → 返回内容
    │   └── 失败 → 添加到黑名单
    │
    ├── 检查文章数量
    │   └── 已达到 5 篇？ → 停止处理
    │
    ▼
Extracted Articles
    │
    ├── 收集所有线程的结果
    │
    ▼
Update tracker (更新最新的时间戳)
    │
    ▼
Output (JSON format, 仅包含成功提取的文章)
```

### 部署和发布

**目标**：支持多种部署方式，包括作为 Python 包发布和独立可执行文件

**发布方案**：

1. **PyPI 包发布**
   - 使用 `setuptools` 或 `poetry` 打包
   - 提供 `yonglelaoren-feedland-parser` 命令行工具
   - 用户可通过 `pip install yonglelaoren-feedland-parser` 安装
   - 配置文件路径：`~/.config/yonglelaoren-feedland-parser/config.json`

2. **独立可执行文件**
   - 使用 `PyInstaller` 打包成单一可执行文件
   - 支持 Windows、macOS、Linux
   - 配置文件与可执行文件同目录或用户配置目录
   - 无需 Python 环境，开箱即用

3. **Docker 容器**
   - 提供 Dockerfile 用于容器化部署
   - 挂载配置文件和数据目录
   - 适合服务器端定时任务

**目录结构（发布版本）**：
```
yonglelaoren-feedland-parser/
├── src/
│   └── yonglelaoren_feedland_parser/    # 实际包名
│       ├── __init__.py
│       ├── config.py
│       ├── opml_parser.py
│       ├── feed_parser.py
│       ├── article_extractor.py
│       ├── deduplicator.py
│       └── tracker.py
├── pyproject.toml          # 现代 Python 项目配置
├── setup.cfg               # setuptools 配置（兼容）
├── README.md               # 使用文档
├── LICENSE                 # 许可证
└── tests/                  # 测试用例
```

**命令行接口**：
```bash
# 作为 PyPI 包安装后
yonglelaoren-feedland-parser --config /path/to/config.json

# 作为可执行文件
./yonglelaoren-feedland-parser --config ./config.json

# 使用默认配置
yonglelaoren-feedland-parser
```

**配置文件优先级**：
1. 命令行 `--config` 参数指定的路径
2. 当前目录的 `config.json`
3. 用户配置目录 `~/.config/yonglelaoren-feedland-parser/config.json`

## Open Questions

1. **配置验证**：是否需要添加配置文件的 schema 验证？
   - 当前设计：运行时检查
   - 未来考虑：使用 JSON Schema 进行验证

2. **输出格式扩展**：是否需要支持多种输出格式？
   - 当前设计：仅支持 JSON 格式输出
   - 未来考虑：支持 CSV、数据库等格式

3. **并发数配置**：线程池的并发数是否应该可配置？
   - 当前设计：固定为 10
   - 未来考虑：添加配置项允许用户自定义

4. **黑名单持久化**：是否需要支持黑名单持久化？
   - 当前设计：运行时黑名单，不持久化
   - 未来考虑：提供可选的持久化功能

5. **内容验证策略**：是否需要调整内容验证的严格度？
   - 当前设计：控制字符比例 ≤ 10%
   - 未来考虑：根据实际情况调整阈值

6. **最大文章数配置**：是否需要支持配置最大文章数？
   - 当前设计：固定为 5 篇
   - 未来考虑：添加配置项允许用户自定义