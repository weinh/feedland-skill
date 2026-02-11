---
name: feedland-summarizer
version: 1.0.0
description: 从 FeedLand 获取最新文章并生成 AI 驱动的内容总结。
metadata:
  emoji: "📰"
  category: "news-aggregation"
---

# FeedLand 文章总结技能

此技能允许代理通过调用 `uvx yonglelaoren-feedland-parser` 脚本解析 FeedLand的RSS/Atom 数据，并对返回的最新文章进行深度总结。

## 使用流程

1. **获取数据**：使用内置脚本或命令获取 FeedLand 文章。
   - 预期输入格式：`uvx yonglelaoren-feedland-parser --config ~/.openclaw/feedland-parser.json > feeds.json`
   - 预期输出格式：`feeds.json`中包含 `feed_url`, `feed_title`, 和 `articles` 文章列表的 JSON。

2. **文章内容处理**：
   - 遍历 `articles` 数组。
   - 提取每篇文章的 `title` (标题), `url` (文章原文), `published` (发布时间), `author` (作者), `content` (内容)。

3. **AI分析总结要求**：
   - **分析要求**：作为一名资深首席技术分析师阅读文章。请避开公关套话，按以下要求分析：
      - **是什么**：帮你定义对象
      - **为什么**：帮你找到动力
      - **会怎么样**：帮你预判结果
   - **相关性分析**：识别文章间的潜在关联或共同话题。
   - **输出模板**：
     ```markdown
     ## 📒[{feed_title}]({feed_url}) 最新动态
     - 📄**文章标题**：[{title}]({url})
     - 👀**是什么**：[在此处生成是什么内容...]
     - ❓**为什么**：[在此处生成为什么内容...]
     - ✅**会怎么样**：[在此处生成会怎么样内容...]
     ----
     ## 🔄相关性分析
     - [在此处生成相关性分析内容...]
     ```

## 约束条件
- 文章内容只从`feeds.json`中获取，不通过程序运行的日志获取。
- `feeds.json`中的内容是空数组，结束当前技能，否则进行AI分享总结并按要求输出。
- 如果 `content` 超过 2000 字，请先提取关键段落再进行总结。
- 必须保留原始文章的 `url` 以供用户追溯。