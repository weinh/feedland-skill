# yonglelaoren-feedland-parser

从 Feedland OPML 解析和提取 RSS/Atom feeds 文章内容的工具。

## 功能特性

- 解析 Feedland OPML 接口，提取所有订阅源
- 支持混合格式的 RSS/Atom feeds
- 每个 feed 最多提取 5 篇最新文章
- 使用 Newspaper3k 和 BeautifulSoup 提取文章内容
- 基于时间戳的去重机制，避免重复提取
- 支持并行处理，提高效率
- 输出 JSON 格式的提取结果

## 安装

### 环境要求

- Python 3.11 或更高版本
- 推荐使用 [uv](https://github.com/astral-sh/uv) 作为包管理器

### 使用 uv 安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/weinh/feedland-skill.git
cd feedland-skill

# 使用 uv 创建虚拟环境（自动使用 Python 3.11+）
uv venv

# 安装依赖
uv pip install -e ".[dev]"

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

**uv 优势**：
- ⚡️ 极快的依赖解析和安装速度
- 🎯 自动管理 Python 版本
- 🔒 精确的依赖锁定（uv.lock）
- 📦 统一的包管理体验

## 配置

创建 `config.json` 配置文件：

```json
{
  "url": "https://feedland.com/opml?screenname=yonglelaoren",
  "threads": 10,
  "his": {}
}
```

**配置说明**：

- `url`: Feedland OPML 接口地址（必需）
- `threads`: 并行处理的线程数（可选，默认值：`min(10, cpu_count() * 2 + 1)`）
- `his`: 每个 feed 的最后提取时间映射（自动维护）

**配置文件优先级**：

1. 命令行 `--config` 参数指定的路径
2. 当前目录的 `config.json`
3. 用户配置目录 `~/.config/yonglelaoren-feedland-parser/config.json`

## 使用

### 基本用法

```bash
uvx yonglelaoren-feedland-parser
```

### 指定配置文件

```bash
uvx yonglelaoren-feedland-parser --config /path/to/config.json
```

### 查看版本

```bash
uvx yonglelaoren-feedland-parser --version
```

### 查看帮助

```bash
uvx yonglelaoren-feedland-parser --help
```

## 输出格式

工具会输出 JSON 格式的提取结果，仅包含成功提取的文章：

```json
[
  {
    "feed_url": "https://example.com/feed.xml",
    "feed_title": "Example Feed",
    "articles": [
      {
        "title": "文章标题",
        "url": "https://example.com/article1",
        "published": "2025-02-09T10:00:00Z",
        "author": "作者",
        "content": "文章主要内容..."
      }
    ]
  }
]
```

提取失败的信息会记录到日志中，不会影响 JSON 输出。

## 依赖

- Python 3.11+
- feedparser >= 6.0.10
- newspaper3k >= 0.2.8
- beautifulsoup4 >= 4.12.0
- requests >= 2.31.0
- lxml >= 4.9.0
- python-dateutil >= 2.8.2

## 开发

### 安装开发依赖

```bash
# 使用 uv（推荐）
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

### 运行测试

```bash
# 使用 uv
uv run pytest

# 或直接运行
pytest
```

### 代码格式化

```bash
# 使用 black
black src/ tests/
```

### 代码检查

```bash
# 类型检查
mypy src/

# 风格检查
flake8 src/ tests/

# 代码覆盖率测试
pytest --cov=src --cov-report=html
```

## 发布

### 构建 distribution 包

```bash
uv build
```

### 发布到 PyPI

```bash
uv publish
```


## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [feedparser](https://github.com/kurtmckee/feedparser)
- [newspaper3k](https://github.com/codelucas/newspaper)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)