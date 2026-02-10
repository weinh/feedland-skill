---
name: feedland-skill
description: 从feedland提取咨询
license: MIT
compatibility: Python 3.11+
metadata:
  author: yonglelaoren
  version: "1.0.1"
  generatedBy: "feedland-skill"
---

## 项目概述

Feedland Parser 专为 Feedland 用户设计，用于从导出的 OPML 文件中批量解析 feeds 并提取文章内容。它具有以下核心特性：

- **OPML 解析**：从 Feedland 导出的 OPML 文件读取订阅列表
- **智能内容提取**：多层回退策略（cloudscraper → newspaper3k → beautifulsoup → feed 描述）
- **运行时域名黑名单**：记录解析失败的域名，跳过后续尝试（仅当前运行有效）
- **历史时间过滤**：只处理新于历史记录的文章
- **内容验证**：检测并拒绝乱码内容
- **并发处理**：支持多线程并行解析
- **进度追踪**：记录已处理文章的哈希值，避免重复

---

## 安装

```bash
pip install yonglelaoren-feedland-parser
```

或使用 uvx 直接运行：

```bash
uvx yonglelaoren-feedland-parser --opml <opml-file> --output <output-file>
```

---

## 使用方法

### 命令行接口

```bash
yonglelaoren-feedland-parser --opml feeds.opml --output articles.json
```

### 参数说明

- `--opml, -o`: OPML 文件路径（必需）
- `--output, -O`: 输出 JSON 文件路径（必需）
- `--max-articles, -m`: 每个 feed 最多提取的文章数（默认：5）
- `--workers, -w`: 并发工作线程数（默认：4）
- `--config, -c`: 配置文件路径（可选）
- `--verbose, -v`: 显示详细日志

### 配置文件

创建 `config.json`：

```json
{
  "max_articles_per_feed": 5,
  "worker_count": 4,
  "timeout": 30,
  "tracker_file": "tracker.json"
}
```

---

## 核心功能

### 1. 文章内容提取流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    文章内容提取流程                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  检查黑名单   │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │ 在黑名单中？              │
              └──────┬──────────┬───────┘
                     │          │
                    是          否
                     │          │
                     ▼          ▼
            ┌────────────┐  ┌──────────────────┐
            │ 使用描述内容 │  │ cloudscraper     │
            └────────────┘  └────────┬─────────┘
                                      │
                               失败？ │ 成功？
                               ┌─────┴─────┐
                               │           │
                               ▼           ▼
                        ┌──────────┐  ┌─────────────┐
                        │ newspaper3k│  │ 内容验证    │
                        └─────┬────┘  └──────┬──────┘
                              │              │
                       失败？ │ 成功？     通过？
                       ┌─────┴─────┐   ┌────┴────┐
                       │           │   │         │
                       ▼           ▼   ▼         ▼
                ┌──────────┐ ┌──────┐ ┌─────┐ ┌────────┐
                │ beautiful│ │ 返回 │ │失败 │ │  返回  │
                │    soup   │ │ 内容 │ │加黑 │ │  内容  │
                └─────┬────┘ └──────┘ └─────┘ └────────┘
                      │
               失败？ │ 成功？
               ┌─────┴─────┐
               │           │
               ▼           ▼
        ┌──────────┐ ┌────────────┐
        │ 使用描述 │ │  内容验证   │
        └──────────┘ └──────┬─────┘
                            │
                     通过？ │ 失败？
                     ┌─────┴─────┐
                     │           │
                     ▼           ▼
              ┌─────────┐  ┌─────────┐
              │ 返回内容 │ │ 失败加黑 │
              └─────────┘  └─────────┘
```

### 2. 域名黑名单

**特性：**
- 运行时有效，不持久化到配置文件
- 线程安全，使用 `threading.Lock`
- 黑名单中的域名直接使用 feed 描述，不尝试 URL 提取

**使用场景：**
```python
from feedland_parser.domain_blacklist import DomainBlacklist

blacklist = DomainBlacklist()
blacklist.add_to_blacklist("https://example.com/article", "频繁触发人类验证")

if blacklist.is_blacklisted("https://example.com/another"):
    # 跳过提取，直接使用描述
    pass
```

### 3. 内容验证

自动检测并拒绝以下问题内容：
- 内容长度 < 50 字符
- 不可打印字符占比 > 10%
- 包含 null 字符
- UTF-8 编码验证失败

### 4. 历史时间过滤

```python
# 只处理新于历史记录的文章
if published_dt <= last_timestamp:
    # 停止处理，文章已是历史内容
    break
```

---

## Python API

### 基础用法

```python
from feedland_parser.opml_parser import parse_opml
from feedland_parser.feed_parser import FeedParser
from feedland_parser.article_extractor import ArticleExtractor
from feedland_parser.domain_blacklist import DomainBlacklist

# 解析 OPML
feeds = parse_opml("feeds.opml")

# 创建黑名单和提取器
blacklist = DomainBlacklist()
extractor = ArticleExtractor(blacklist=blacklist)

# 解析单个 feed
parser = FeedParser(extractor=extractor)
articles = parser.parse_feed(feed_info, last_timestamp=None)
```

### 高级用法

```python
from feedland_parser.parallel_processor import ParallelProcessor
from feedland_parser.tracker import Tracker

# 创建追踪器
tracker = Tracker("tracker.json")

# 并行处理多个 feeds
processor = ParallelProcessor(
    feed_parser=parser,
    worker_count=4,
    tracker=tracker
)

results = processor.process(feeds)
```

---

## 输出格式

```json
{
  "articles": [
    {
      "title": "文章标题",
      "url": "https://example.com/article",
      "content": "文章内容...",
      "published": "2026-02-10T10:00:00Z",
      "feed_title": "Feed 标题",
      "feed_url": "https://example.com/feed.xml"
    }
  ],
  "stats": {
    "total_feeds": 10,
    "successful_feeds": 8,
    "failed_feeds": 2,
    "total_articles": 50,
    "blacklisted_domains": 3
  }
}
```

---

## 常见问题

### 1. 如何启用详细日志？

```bash
yonglelaoren-feedland-parser --opml feeds.opml --output articles.json --verbose
```

### 2. 黑名单会保存吗？

不会。黑名单仅在当前运行期间有效，程序结束后自动清空。

### 3. 如何处理反爬虫网站？

使用 `cloudscraper` 作为第一层提取器，可以绕过 Cloudflare 保护。如果仍然失败，域名会被加入黑名单。

### 4. 如何提取更多文章？

```bash
yonglelaoren-feedland-parser --opml feeds.opml --output articles.json --max-articles 10
```

---

## 依赖

- feedparser>=6.0.10
- newspaper3k>=0.2.8
- beautifulsoup4>=4.12.0
- requests>=2.31.0
- lxml>=4.9.0
- lxml-html-clean>=0.1.0
- python-dateutil>=2.8.2
- cloudscraper>=1.2.71

---

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/
```

---

## 架构设计

### 模块说明

| 模块 | 功能 |
|------|------|
| `opml_parser.py` | 解析 OPML 文件，提取订阅列表 |
| `feed_parser.py` | 解析单个 feed，过滤历史文章 |
| `article_extractor.py` | 多层策略提取文章内容 |
| `domain_blacklist.py` | 运行时域名黑名单管理 |
| `deduplicator.py` | 文章去重（基于 URL 和内容哈希） |
| `tracker.py` | 追踪已处理文章和时间戳 |
| `parallel_processor.py` | 并发处理多个 feeds |
| `config.py` | 配置管理 |
| `cli.py` | 命令行接口 |

---

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 许可证

MIT License - 详见 LICENSE 文件

---

## 联系方式

- 作者: yonglelaoren
- 项目主页: https://github.com/yonglelaoren/yonglelaoren-feedland-parser
- 问题反馈: https://github.com/yonglelaoren/yonglelaoren-feedland-parser/issues

---

## 更新日志

### 1.0.1 (2026-02-10)
- 添加 lxml-html-clean 依赖以支持 lxml 5.0+
- 修复 ImportError 问题

### 1.0.0 (2026-02-10)
- 初始版本发布
- 支持 OPML 解析、文章提取、域名黑名单
- 支持历史时间过滤、并发处理