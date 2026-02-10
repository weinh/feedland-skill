#!/usr/bin/env python3
"""集成测试脚本 - 测试完整的 CLI 工作流程"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feedland_parser import Config, OPMLParser, FeedParser, ArticleExtractor, FeedTracker, Deduplicator, ParallelFeedProcessor


def test_cli_workflow():
    """测试完整的 CLI 工作流程"""
    print("=" * 60)
    print("集成测试: CLI 工作流程")
    print("=" * 60)

    # 使用测试配置文件
    test_config_path = Path(__file__).parent / "test_config.json"

    # 1. 加载配置
    print("\n1️⃣ 加载配置...")
    config = Config(str(test_config_path))
    config.load()
    print(f"   ✅ 配置加载成功: {config.url}")
    print(f"   ✅ 线程数: {config.threads}")

    # 2. 解析 OPML
    print("\n2️⃣ 解析 OPML...")
    opml_parser = OPMLParser()
    feed_infos = opml_parser.parse_opml(config.url)
    print(f"   ✅ 找到 {len(feed_infos)} 个 feeds")

    if not feed_infos:
        print("   ⚠️  未找到任何 feeds，测试终止")
        return False

    # 3. 初始化处理器
    print("\n3️⃣ 初始化处理器...")
    article_extractor = ArticleExtractor()
    tracker = FeedTracker(config)
    tracker.load_history()
    deduplicator = Deduplicator(tracker)
    feed_parser = FeedParser(article_extractor, deduplicator, max_articles=2)  # 只提取 2 篇用于测试
    print("   ✅ 处理器初始化完成")

    # 4. 并行处理（限制数量以加快测试）
    print("\n4️⃣ 并行处理 feeds（限制为 2 个用于测试）...")
    test_feeds = feed_infos[:2]  # 只测试前 2 个 feeds

    processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=config.threads)

    results = processor.process_feeds_parallel(test_feeds)

    # 5. 生成摘要
    summary = processor.get_summary(results)
    print(f"\n5️⃣ 处理摘要:")
    print(f"   📊 总 feeds: {summary['total_feeds']}")
    print(f"   ✅ 成功: {summary['successful_feeds']}")
    print(f"   ❌ 失败: {summary['failed_feeds']}")
    print(f"   📄 总文章: {summary['total_articles']}")

    # 6. 获取成功的结果
    successful = processor.get_successful_results(results)
    if successful:
        print(f"\n6️⃣ 成功的 feeds:")
        for result in successful:
            print(f"   ✅ {result.feed_info.title}: {len(result.articles)} 篇文章")

    # 7. 获取失败的结果
    failed = processor.get_failed_results(results)
    if failed:
        print(f"\n❌ 失败的 feeds:")
        for result in failed:
            print(f"   ❌ {result.feed_info.title}: {result.error}")

    # 8. 测试输出格式
    print(f"\n7️⃣ 测试输出格式...")
    output = processor.get_all_articles(results)
    if output:
        print(f"   ✅ 输出格式验证通过，共 {len(output)} 篇文章")

        # 显示第一篇文章的信息
        if output:
            article = output[0]
            print(f"\n   📝 示例文章:")
            print(f"      标题: {article.get('title', 'Unknown')}")
            print(f"      URL: {article.get('url', 'Unknown')}")

    print("\n" + "=" * 60)
    print("✅ 集成测试完成！")
    print("=" * 60)

    return summary['successful_feeds'] > 0


if __name__ == "__main__":
    try:
        success = test_cli_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)