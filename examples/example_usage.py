#!/usr/bin/env python3
"""使用示例：如何使用 yonglelaoren-feedland-parser API"""

import json
from feedland_parser import (
    Config,
    OPMLParser,
    FeedParser,
    ArticleExtractor,
    FeedTracker,
    Deduplicator,
    ParallelFeedProcessor,
)


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 1. 加载配置
    config = Config("config.json")
    config.load()

    print(f"Feedland OPML URL: {config.url}")
    print(f"线程数: {config.threads}")

    # 2. 解析 OPML
    opml_parser = OPMLParser()
    feed_infos = opml_parser.parse_opml(config.url)

    print(f"找到 {len(feed_infos)} 个订阅源")

    # 3. 初始化处理器
    article_extractor = ArticleExtractor()
    tracker = FeedTracker(config)
    tracker.load_history()
    deduplicator = Deduplicator(tracker)
    feed_parser = FeedParser(article_extractor, deduplicator)

    # 4. 并行处理
    processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=config.threads)
    results = processor.process_feeds_parallel(feed_infos)

    # 5. 获取结果
    summary = processor.get_summary(results)
    print(f"处理完成: {summary['successful_feeds']}/{summary['total_feeds']} 成功")
    print(f"共提取 {summary['total_articles']} 篇文章")

    # 6. 保存到 JSON
    output = processor.get_all_articles(results)
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("结果已保存到 output.json")


def example_custom_extractor():
    """自定义文章提取器示例"""
    print("\n=== 自定义文章提取器示例 ===")

    from feedland_parser import ArticleExtractor

    extractor = ArticleExtractor()

    # 提取文章
    article = extractor.extract("https://example.com/article")

    if article:
        print(f"标题: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"作者: {article['author']}")
        print(f"发布时间: {article['published']}")
        print(f"内容长度: {len(article['content'])}")
    else:
        print("提取失败")


def example_feed_parsing():
    """单独解析 feed 示例"""
    print("\n=== 单独解析 Feed 示例 ===")

    from feedland_parser import (
        ArticleExtractor,
        Deduplicator,
        FeedParser,
        FeedTracker,
    )
    from feedland_parser.opml_parser import FeedInfo

    # 创建组件
    extractor = ArticleExtractor()
    tracker = FeedTracker(None)  # 如果不需要跟踪历史
    deduplicator = Deduplicator(tracker)
    parser = FeedParser(extractor, deduplicator)

    # 解析单个 feed
    feed_info = FeedInfo(
        url="https://example.com/feed.xml", title="Example Feed", feed_type="RSS"
    )
    result = parser.parse_feed(feed_info)

    if result.success:
        print(f"成功提取 {len(result.articles)} 篇文章")
        for article in result.articles:
            print(f"  - {article['title']}")
    else:
        print(f"解析失败: {result.error}")


def example_progress_callback():
    """使用进度回调示例"""
    print("\n=== 进度回调示例 ===")

    config = Config("config.json")
    config.load()

    opml_parser = OPMLParser()
    feed_infos = opml_parser.parse_opml(config.url)

    # 只取前 3 个 feeds 进行演示
    feed_infos = feed_infos[:3]

    article_extractor = ArticleExtractor()
    tracker = FeedTracker(config)
    tracker.load_history()
    deduplicator = Deduplicator(tracker)
    feed_parser = FeedParser(article_extractor, deduplicator)
    processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=2)

    # 定义进度回调
    def progress_callback(current, total, result):
        print(f"进度: {current}/{total} - {result.feed_info.title}")
        if result.success:
            print(f"  提取了 {len(result.articles)} 篇文章")

    # 使用进度回调
    results = processor.process_feeds_parallel(feed_infos, progress_callback=progress_callback)


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    config = Config("config.json")
    config.load()

    opml_parser = OPMLParser()

    try:
        feed_infos = opml_parser.parse_opml(config.url)
    except Exception as e:
        print(f"OPML 解析失败: {e}")
        return

    article_extractor = ArticleExtractor()
    tracker = FeedTracker(config)
    tracker.load_history()
    deduplicator = Deduplicator(tracker)
    feed_parser = FeedParser(article_extractor, deduplicator)
    processor = ParallelFeedProcessor(feed_parser, tracker)

    results = processor.process_feeds_parallel(feed_infos)

    # 获取失败的结果
    failed_results = processor.get_failed_results(results)

    if failed_results:
        print(f"有 {len(failed_results)} 个 feeds 解析失败:")
        for result in failed_results:
            print(f"  - {result.feed_info.title}: {result.error}")
    else:
        print("所有 feeds 解析成功")


if __name__ == "__main__":
    print("yonglelaoren-feedland-parser 使用示例\n")

    # 注意：这些示例需要有效的 config.json 文件和网络连接
    # 如果没有 config.json，可以取消下面的注释来创建一个示例文件

    # import json
    # example_config = {
    #     "url": "https://feedland.com/opml?screenname=yonglelaoren",
    #     "threads": 2,
    #     "his": {}
    # }
    # with open("config.json", "w") as f:
    #     json.dump(example_config, f)

    try:
        example_basic_usage()
    except Exception as e:
        print(f"基本使用示例失败: {e}")

    try:
        example_feed_parsing()
    except Exception as e:
        print(f"Feed 解析示例失败: {e}")

    # 由于需要实际的网络请求，这些示例可能会失败
    # try:
    #     example_custom_extractor()
    # except Exception as e:
    #     print(f"自定义提取器示例失败: {e}")

    # try:
    #     example_progress_callback()
    # except Exception as e:
    #     print(f"进度回调示例失败: {e}")

    # try:
    #     example_error_handling()
    # except Exception as e:
    #     print(f"错误处理示例失败: {e}")
