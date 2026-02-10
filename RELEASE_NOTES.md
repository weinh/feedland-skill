# yonglelaoren-feedland-parser v1.0.0 发布说明

## 🎉 首个稳定版本发布！

我们很高兴地宣布 `yonglelaoren-feedland-parser` 的首个稳定版本 v1.0.0 现已发布！

## 📦 安装

### 通过 pip 安装

```bash
pip install yonglelaoren-feedland-parser
```

### 从源码安装

```bash
git clone https://github.com/yonglelaoren/yonglelaoren-feedland-parser.git
cd yonglelaoren-feedland-parser
pip install -e .
```

### Docker

```bash
docker pull yonglelaoren/feedland-parser
docker run -v ./config.json:/app/config.json yonglelaoren/feedland-parser
```

## ✨ 主要功能

- ✅ 解析 Feedland OPML 接口，提取所有订阅源
- ✅ 支持多种 feed 格式（RSS 2.0、RSS 1.0、Atom）
- ✅ 使用 Newspaper3k 和 BeautifulSoup 提取文章内容
- ✅ 基于时间戳的去重机制，避免重复处理
- ✅ 并行处理多个 feeds，提高效率
- ✅ 命令行接口，易于使用
- ✅ JSON 格式输出，便于集成
- ✅ 完善的错误处理和日志记录
- ✅ Docker 和 PyInstaller 支持

## 🚀 快速开始

1. 创建配置文件 `config.json`：

```json
{
  "url": "https://feedland.com/opml?screenname=yonglelaoren",
  "threads": 10,
  "his": {}
}
```

2. 运行程序：

```bash
yonglelaoren-feedland-parser --config config.json
```

3. 查看提取结果（JSON 格式）

## 📖 文档

- [README](https://github.com/yonglelaoren/yonglelaoren-feedland-parser#readme)
- [API 文档](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/blob/main/src/yonglelaoren_feedland_parser/)
- [使用示例](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/tree/main/examples)
- [贡献指南](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/blob/main/CONTRIBUTING.md)

## 🐛 已知问题

无

## 🔄 变更日志

详见 [CHANGELOG.md](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/blob/main/CHANGELOG.md)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和使用者！

特别感谢以下开源项目：
- [feedparser](https://github.com/kurtmckee/feedparser)
- [newspaper3k](https://github.com/codelucas/newspaper)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

## 📧 联系方式

- 作者: yonglelaoren
- 邮箱: yonglelaoren@example.com
- GitHub: https://github.com/yonglelaoren

## 📄 许可证

MIT License - 详见 [LICENSE](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/blob/main/LICENSE) 文件

---

**感谢使用 yonglelaoren-feedland-parser！** 🎊