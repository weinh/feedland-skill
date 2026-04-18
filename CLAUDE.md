# CLAUDE.md

这个文件为 Claude Code (claude.ai/code) 提供在此仓库中工作的指导。

## 项目概述

这是一个 Python 工具，用于从 Feedland OPML 解析 RSS/Atom feeds 并使用多种提取策略提取文章内容。它实现了智能 URL 处理（例如从搜狗微信搜索结果中提取真实 URL）、域名黑名单管理和并行处理以提高效率。

## 开发环境

**包管理器**：本项目使用 [uv](https://github.com/astral-sh/uv) 作为包管理器（不是 pip）。

```bash
# 安装依赖
uv pip install -e ".[dev]"

# 运行工具
uvx yonglelaoren-feedland-parser

# 使用指定配置文件运行
uvx yonglelaoren-feedland-parser --config /path/to/config.json
```

**Python 版本**：需要 Python 3.11+

## 常用开发命令

### 测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_filter.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 代码质量
```bash
# 使用 Black 格式化代码（行长度：88）
black src/ tests/

# 使用 mypy 进行类型检查
mypy src/

# 使用 flake8 进行风格检查
flake8 src/ tests/
```

### 构建和发布
```bash
# 构建分发包
uv build

# 发布到 PyPI
uv publish
```

## 架构设计

代码库采用模块化流水线架构：

### 核心组件

1. **CLI 入口** ([cli.py](src/feedland_parser/cli.py))
   - 参数解析和配置加载
   - 设置可配置保留期的滚动日志
   - 编排整个处理流程

2. **OPML 解析器** ([opml_parser.py](src/feedland_parser/opml_parser.py))
   - 下载并解析 Feedland OPML 文档
   - 提取 feed URLs 和元数据
   - 自动检测 feed 类型（RSS/Atom）

3. **Feed 解析器** ([feed_parser.py](src/feedland_parser/feed_parser.py))
   - 使用 feedparser 解析单个 RSS/Atom feeds
   - 实现重试机制（最多 3 次）
   - 从搜狗微信搜索页面提取真实 URLs
   - 使用优先级策略生成文章 ID：发布时间戳 > guid > link > hash

4. **文章提取器** ([article_extractor.py](src/feedland_parser/article_extractor.py))
   - 多策略内容提取（优先级顺序）：
     1. Readability 算法（智能内容提取）
     2. Newspaper3k（NLP 分析）
     3. CSS 选择器（回退方案）
     4. 描述内容（最终回退）
   - 网络错误检测以跳过失败的域名
   - CloudScraper 支持反爬虫保护

5. **过滤器** ([filter.py](src/feedland_parser/filter.py))
   - 使用文章 ID 进行线程安全的去重
   - 维护 feed 历史记录（最后处理的文章 ID）
   - 支持基于 ID 和时间戳的比较

6. **域名黑名单** ([domain_blacklist.py](src/feedland_parser/domain_blacklist.py))
   - 线程安全的域名黑名单管理
   - 跟踪黑名单域名的元数据
   - 永久黑名单包括 `weixin.sogou.com`

7. **并行处理器** ([parallel_processor.py](src/feedland_parser/parallel_processor.py))
   - 基于 ThreadPoolExecutor 的并行处理
   - 线程安全的过滤器更新
   - 进度回调用于监控

### 数据流

```
OPML URL → OPML 解析器 → Feed URLs → Feed 解析器 → 文章 URLs → 
文章提取器 → 过滤器（去重） → 并行处理 → JSON 输出
```

## 配置

工具需要 `config.json` 配置文件：

```json
{
  "url": "https://feedland.com/opml?screenname=yonglelaoren",
  "threads": 10,
  "log_days": 3,
  "log_dir": "~/.feedland/logs",
  "result_file": "~/.feedland/results.json",
  "his": {}
}
```

**配置优先级**：`--config` 参数 > `./config.json` > `~/.config/yonglelaoren-feedland-parser/config.json`

## 关键实现细节

### 文章 ID 策略
去重系统使用基于优先级的 ID 策略：
1. **发布时间戳**（最可靠）- 用于时间比较
2. **GUID** - RSS 2.0 标准标识符
3. **Link** - 无 GUID 的 feed 的回退方案
4. **Hash** - 最终回退方案（title+link 的 MD5）

### 搜狗微信 URL 处理
对 `weixin.sogou.com` URLs 的特殊处理：
- 检测搜狗搜索结果页面
- 从 HTML 内容中提取真实的 `mp.weixin.qq.com` URLs
- 将 `weixin.sogou.com` 添加到永久黑名单

### 线程安全
关键组件使用 threading.Lock：
- 过滤器历史记录更新
- 域名黑名单操作
- 并行处理器协调

### 日志架构
- 按天轮转的滚动日志
- 可配置的保留期（默认：3 天）
- 不同组件的独立日志级别
- 第三方库噪音降低（urllib3、requests）

## 开发工作流

本项目使用 **OpenSpec** 进行规范驱动的开发。完整的工作流文档见 [AGENTS.md](AGENTS.md)。

可用命令：
- `/opsx:new <name>` - 创建新变更
- `/opsx:continue` - 继续下一个文档
- `/opsx:apply <name>` - 实现任务
- `/opsx:verify <name>` - 验证实现
- `/opsx:archive <name>` - 归档已完成的变更
- `/opsx:explore` - 探索模式

## 测试策略

- **单元测试**：每个模块都有对应的 `test_*.py` 文件
- **集成测试**：`test_cli_extended.py` 覆盖端到端工作流
- **并发测试**：`test_domain_blacklist_concurrent.py` 用于线程安全测试
- **覆盖率目标**：运行 `pytest --cov=src --cov-report=html` 并检查 `htmlcov/index.html`

## 代码风格

- **行长度**：88 字符（Black 默认值）
- **类型提示**：必需（mypy 配置 `disallow_untyped_defs = true`）
- **文档字符串**：面向用户的代码使用中文文档
- **日志**：使用模块级别的 logger，不使用 root logger

## 依赖项

主要外部库：
- **feedparser** (≥6.0.10)：RSS/Atom feed 解析
- **newspaper3k** (≥0.2.8)：文章内容提取
- **beautifulsoup4** (≥4.12.0)：HTML 解析
- **readability-lxml** (≥0.8.1)：智能内容提取
- **cloudscraper** (≥1.2.71)：反爬虫保护（可选）
- **python-dateutil** (≥2.8.2)：日期解析
