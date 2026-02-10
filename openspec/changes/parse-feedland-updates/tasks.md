## 1. 项目初始化

- [x] 1.1 创建项目目录结构 `yonglelaoren-feedland-parser/src/yonglelaoren_feedland_parser/`
- [x] 1.2 创建 `pyproject.toml` 配置文件，定义项目元数据和依赖（feedparser, newspaper3k, beautifulsoup4, requests, lxml, python-dateutil）
- [x] 1.3 创建 `config.json` 示例配置文件，包含 url、threads 和 his 字段
- [x] 1.4 创建 `README.md` 项目文档，说明安装和使用方法
- [x] 1.5 创建 `src/yonglelaoren_feedland_parser/__init__.py` 包初始化文件

## 2. 配置管理模块 (config.py)

- [x] 2.1 实现 `Config` 类，用于读取和解析 config.json 文件
- [x] 2.2 实现配置文件路径查找逻辑（命令行参数、当前目录、用户配置目录）
- [x] 2.3 实现线程数配置读取和默认值处理（min(10, cpu_count() * 2 + 1)）
- [x] 2.4 实现文件锁机制，用于防止并发写入冲突
- [x] 2.5 实现配置保存功能，更新 config.json 中的 his 字段
- [x] 2.6 添加配置验证，确保必要字段存在
- [x] 2.7 为 config 模块编写单元测试

## 3. OPML 解析模块 (opml_parser.py)

- [x] 3.1 实现 `OPMLParser` 类，用于解析 OPML 文档
- [x] 3.2 实现 `parse_opml()` 方法，从 OPML URL 提取 feed 列表
- [x] 3.3 实现 feed 元数据提取（标题、URL、类型）
- [x] 3.4 添加对缺失标题的处理（使用 URL 作为备用）
- [x] 3.5 添加错误处理（网络错误、无效 OPML、空响应）
- [x] 3.6 为 opml_parser 模块编写单元测试

## 4. 文章内容提取模块 (article_extractor.py)

- [x] 4.1 实现 `ArticleExtractor` 类，用于提取文章内容
- [x] 4.2 实现 `extract_with_cloudscraper()` 方法，使用 cloudscraper 提取内容（首选方案，可绕过 Cloudflare）
- [x] 4.3 实现 `extract_with_newspaper3k()` 方法，使用 Newspaper3k 提取内容
- [x] 4.4 实现 `extract_with_beautifulsoup()` 方法，作为最后的回退方案
- [x] 4.5 实现文章元数据提取（标题、URL、发布日期、作者）
- [x] 4.6 添加时间戳解析功能，支持多种格式（使用 dateutil.parser）
- [x] 4.7 添加对缺失发布日期的处理
- [x] 4.8 实现描述内容回退机制，当 URL 提取失败时使用 feed 中的描述内容
- [x] 4.9 实现内容验证功能 `_is_content_valid()`，检测并拒绝乱码内容
- [x] 4.10 添加乱码检测逻辑（控制字符比例、null 字符、编码验证）
- [x] 4.11 集成域名黑名单，在黑名单中的域名直接使用描述内容
- [x] 4.12 添加多层回退策略：cloudscraper → newspaper3k → beautifulsoup → 描述内容
- [x] 4.13 添加对付费墙和登录页面的处理
- [x] 4.14 添加 HTML 解析错误处理
- [x] 4.15 为 article_extractor 模块编写单元测试（包括乱码检测和描述回退测试）

## 5. 时间戳跟踪模块 (tracker.py)

- [x] 5.1 实现 `FeedTracker` 类，用于跟踪每个 feed 的最后提取时间
- [x] 5.2 实现 `load_history()` 方法，从 config.json 的 his 字段加载历史记录
- [x] 5.3 实现 `save_history()` 方法，将历史记录保存到 config.json（使用文件锁）
- [x] 5.4 实现 `get_last_timestamp()` 方法，获取指定 feed 的最后提取时间
- [x] 5.5 实现 `update_timestamp()` 方法，更新指定 feed 的最后提取时间
- [x] 5.6 添加对缺少 his 字段的处理（初始化为空字典）
- [x] 5.7 为 tracker 模块编写单元测试

## 6. 去重逻辑模块 (deduplicator.py)

- [x] 6.1 实现 `Deduplicator` 类，用于文章去重
- [x] 6.2 实现 `is_new_article()` 方法，检查文章是否已处理
- [x] 6.3 实现基于 feed 时间戳的过滤逻辑
- [x] 6.4 添加 URL 标准化功能（移除跟踪参数）
- [x] 6.5 添加对缺少时间戳的处理
- [x] 6.6 添加去重失败时的容错处理
- [x] 6.7 为 deduplicator 模块编写单元测试

## 7. 域名黑名单模块 (domain_blacklist.py)

- [x] 7.1 实现 `DomainBlacklist` 类，用于管理和查询解析失败的域名
- [x] 7.2 实现 `is_blacklisted()` 方法，检查域名是否在黑名单中
- [x] 7.3 实现 `add_to_blacklist()` 方法，将失败域名添加到黑名单
- [x] 7.4 实现 `get_domain_from_url()` 方法，从 URL 提取域名（自动移除 www. 前缀）
- [x] 7.5 实现黑名单元数据管理（添加时间、失败次数、失败原因）
- [x] 7.6 使用 `threading.Lock` 实现线程安全的黑名单操作
- [x] 7.7 实现 `cleanup_old_entries()` 方法，定期移除旧条目（可选）
- [x] 7.8 运行时黑名单（不持久化到配置文件），每次启动都是空的
- [x] 7.9 实现黑名单添加逻辑：URL 失败就添加黑名单（不管有没有描述内容）
- [x] 7.10 为 domain_blacklist 模块编写单元测试（包括并发测试）

## 8. Feed 解析模块 (feed_parser.py)

- [x] 8.1 实现 `FeedParser` 类，用于解析单个 feed
- [x] 8.2 实现 `parse_feed()` 方法，使用 feedparser 解析 RSS/Atom feed
- [x] 8.3 实现文章数量限制（最多 5 篇成功的文章）
- [x] 8.4 实现文章按时间排序
- [x] 8.5 集成 ArticleExtractor 提取文章内容
- [x] 8.6 集成 Deduplicator 进行去重过滤
- [x] 8.7 集成 DomainBlacklist，检查文章 URL 域名是否在黑名单中
- [x] 8.8 当文章解析失败时，将域名添加到黑名单
- [x] 8.9 实现描述内容提取方法 `_get_description()`，从条目中获取描述或摘要
- [x] 8.10 将描述内容传递给 ArticleExtractor 作为回退方案
- [x] 8.11 实现历史时间过滤：不处理发布时间不晚于历史时间的文章
- [x] 8.12 实现处理流程优化：达到 5 篇或达到历史时间时停止处理
- [x] 8.13 添加对 RSS 2.0、RSS 1.0、Atom 格式的支持
- [x] 8.14 添加网络超时和重试机制（最多 3 次，超时 10 秒）
- [x] 8.15 添加 HTTP 错误处理（4xx、5xx）
- [x] 8.16 添加 feed 格式错误处理
- [x] 8.17 添加黑名单检查日志，记录跳过的域名
- [x] 8.18 添加内容验证日志，记录乱码检测
- [x] 8.19 为 feed_parser 模块编写单元测试

## 9. 并行处理集成

- [x] 9.1 使用 `ThreadPoolExecutor` 实现并行处理多个 feeds
- [x] 9.2 实现线程池大小配置（从 config.json 读取）
- [x] 9.3 使用 `concurrent.futures.as_completed` 收集结果
- [x] 9.4 实现线程安全的 config.json 更新（使用文件锁）
- [x] 9.5 添加并行处理的错误日志记录
- [x] 9.6 为并行处理编写集成测试

## 10. 命令行接口 (任务 10.1-10.9)

- [x] 10.1 实现命令行参数解析（使用 argparse）
- [x] 10.2 实现 `--config` 参数，指定配置文件路径
- [x] 10.3 实现 `--version` 参数，显示版本号
- [x] 10.4 实现 `--help` 参数，显示帮助信息
- [x] 10.5 实现主流程：加载配置 → 解析 OPML → 并行处理 feeds → 输出 JSON
- [x] 10.6 实现 JSON 格式输出（仅包含成功提取的文章）
- [x] 10.7 添加日志系统，记录提取失败信息
- [x] 10.8 添加进度显示（处理了多少 feeds）
- [x] 10.9 为 CLI 编写集成测试

## 11. 打包和发布 (任务 11.1-11.8)

- [x] 11.1 在 `pyproject.toml` 中配置项目元数据（名称、版本、作者等）
- [x] 11.2 配置命令行入口点 `yonglelaoren-feedland-parser`
- [x] 11.3 编写 `setup.cfg` 用于 setuptools 兼容
- [ ] 11.4 测试本地安装 `pip install -e .`
- [x] 11.5 创建 `Dockerfile` 用于容器化部署
- [x] 11.6 创建 PyInstaller 配置文件（用于打包可执行文件）
- [x] 11.7 编写 LICENSE 许可证文件
- [ ] 11.8 测试 Windows、macOS、Linux 平台的兼容性

## 12. 文档和示例 (任务 12.1-12.6)

- [x] 12.1 完善 README.md，包含安装说明、使用示例、配置说明
- [x] 12.2 创建 `config.example.json` 配置示例文件
- [x] 12.3 编写 CONTRIBUTING.md 贡献指南
- [x] 12.4 编写 CHANGELOG.md 变更日志
- [x] 12.5 添加代码注释和文档字符串（遵循 Google 风格）
- [x] 12.6 创建使用示例脚本

## 13. 测试和质量保证

- [x] 13.1 编写端到端测试（E2E），测试完整流程
- [x] 13.2 编写性能测试，测试并行处理效率
- [x] 13.3 添加代码覆盖率测试（目标 80%+）
- [ ] 13.4 使用 pylint 或 flake8 进行代码风格检查
- [ ] 13.5 使用 mypy 进行类型检查
- [ ] 13.6 修复所有测试发现的问题
- [ ] 13.7 确保所有测试通过

## 14. 文章解析流程和策略

- [x] 14.1 实现多层回退提取策略：cloudscraper → newspaper3k → beautifulsoup → 描述内容
- [x] 14.2 实现域名黑名单机制，避免重复解析失败的域名
- [x] 14.3 实现内容验证机制，自动检测和拒绝乱码内容
- [x] 14.4 实现历史时间过滤，避免处理旧文章
- [x] 14.5 实现最大文章数限制（5 篇），避免过度处理
- [x] 14.6 实现线程安全的黑名单操作，支持并行处理
- [x] 14.7 实现描述内容提取和传递，确保即使 URL 失败也能获取内容
- [x] 14.8 为文章解析流程编写集成测试

## 15. 文章解析详细流程

### 15.1 黑名单检查阶段
- 检查文章 URL 的域名是否在黑名单中
- 如果在黑名单中：
  - 有描述内容（≥50 字符）→ 直接使用描述内容，返回成功
  - 无描述内容或描述太短 → 跳过解析，返回失败

### 15.2 URL 内容提取阶段
- 优先使用 cloudscraper 提取（可绕过 Cloudflare 保护）
- 如果 cloudscraper 失败，使用 newspaper3k 提取
- 如果 newspaper3k 失败，使用 BeautifulSoup 提取
- 每次提取成功后都进行内容验证：
  - 检查内容长度（≥100 字符）
  - 检查不可打印字符比例（≤10%）
  - 检查 null 字符（0 个）
  - 检查编码有效性（UTF-8）
- 如果内容验证失败，继续尝试下一个提取方法

### 15.3 描述内容回退阶段
- 如果所有 URL 提取方法都失败，尝试使用描述内容
- 验证描述内容（≥50 字符，无乱码）
- 如果描述内容有效：
  - 返回成功
  - 将域名添加到黑名单（因为 URL 提取失败）
- 如果描述内容无效：
  - 返回失败
  - 将域名添加到黑名单（因为 URL 提取失败且无有效内容）

### 15.4 黑名单管理规则
- **添加条件**：URL 提取失败就添加黑名单（不管有没有描述内容）
- **移除条件**：程序退出后自动清空（运行时黑名单，不持久化）
- **线程安全**：使用 `threading.Lock` 保护所有黑名单操作
- **域名提取**：自动移除 www. 前缀，统一域名格式

### 15.5 Feed 处理流程
- 按顺序遍历 feed 条目
- 检查是否已达到 5 篇成功的文章
- 检查文章发布时间是否不晚于历史时间
- 如果达到任一停止条件，停止处理
- 记录总共检查的条目数和最终成功的文章数

## 16. 发布准备

- [x] 16.1 更新版本号到 1.0.0
- [x] 16.2 生成发布说明
- [ ] 16.3 构建 distribution 包（运行: `python -m build`）
- [ ] 16.4 在测试 PyPI 环境测试发布
- [ ] 16.5 发布到 PyPI（运行: `twine upload dist/*`）
- [x] 16.6 创建 GitHub Release