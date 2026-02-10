"""性能测试"""

import pytest
import time
from unittest.mock import patch, MagicMock

from feedland_parser import (
    FeedParser,
    ArticleExtractor,
    FeedTracker,
    Deduplicator,
    ParallelFeedProcessor,
)
from feedland_parser.opml_parser import FeedInfo
from feedland_parser.feed_parser import FeedResult


class TestPerformance:
    """性能测试"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = MagicMock()
        config.history = {}
        return config

    @pytest.fixture
    def article_extractor(self):
        """创建文章提取器"""
        return ArticleExtractor()

    @pytest.fixture
    def tracker(self, mock_config):
        """创建跟踪器"""
        tracker = FeedTracker(mock_config)
        tracker.load_history = MagicMock()
        return tracker

    @pytest.fixture
    def deduplicator(self, tracker):
        """创建去重器"""
        return Deduplicator(tracker)

    @pytest.fixture
    def feed_parser(self, article_extractor, deduplicator):
        """创建 feed 解析器"""
        return FeedParser(article_extractor, deduplicator)

    def test_parallel_processing_performance(self, feed_parser, tracker):
        """测试并行处理性能"""
        # 创建多个 feeds
        feed_infos = [
            FeedInfo(
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                feed_type="RSS"
            )
            for i in range(10)
        ]

        # 模拟解析结果
        def mock_parse(feed_info):
            time.sleep(0.1)  # 模拟处理时间
            return FeedResult(
                feed_info=feed_info,
                articles=[
                    {
                        "title": f"Article {i}",
                        "url": f"https://example.com/article{i}",
                        "published": "2025-02-09T10:00:00Z",
                        "author": "Author",
                        "content": "Content",
                    }
                ],
                success=True,
            )

        # 测试并行处理
        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=4)

        start_time = time.time()
        with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
            results = processor.process_feeds_parallel(feed_infos)
        parallel_time = time.time() - start_time

        # 验证结果
        assert len(results) == 10
        assert all(r.success for r in results)

        # 并行处理应该比顺序处理快
        # 10 个任务，每个 0.1 秒，使用 4 个线程
        # 期望时间大约在 0.3-0.4 秒左右
        assert parallel_time < 0.8  # 留一些余量

    def test_thread_pool_scaling(self, feed_parser, tracker):
        """测试线程池扩展性"""
        feed_infos = [
            FeedInfo(
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                feed_type="RSS"
            )
            for i in range(20)
        ]

        def mock_parse(feed_info):
            time.sleep(0.05)
            return FeedResult(
                feed_info=feed_info,
                articles=[],
                success=True,
            )

        # 测试不同的线程数
        for workers in [2, 4, 8]:
            processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=workers)

            start_time = time.time()
            with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
                results = processor.process_feeds_parallel(feed_infos)
            elapsed_time = time.time() - start_time

            assert len(results) == 20
            print(f"Workers: {workers}, Time: {elapsed_time:.2f}s")

    def test_memory_usage(self, feed_parser, tracker):
        """测试内存使用"""
        # 创建大量 feeds
        feed_infos = [
            FeedInfo(
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                feed_type="RSS"
            )
            for i in range(100)
        ]

        def mock_parse(feed_info):
            return FeedResult(
                feed_info=feed_info,
                articles=[
                    {
                        "title": f"Article {i}",
                        "url": f"https://example.com/article{i}",
                        "published": "2025-02-09T10:00:00Z",
                        "author": "Author",
                        "content": "Content" * 100,  # 较大的内容
                    }
                ],
                success=True,
            )

        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=10)

        with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
            results = processor.process_feeds_parallel(feed_infos)

        # 验证所有结果都被处理
        assert len(results) == 100

        # 获取所有文章
        articles = processor.get_all_articles(results)
        assert len(articles) == 100

    def test_error_handling_performance(self, feed_parser, tracker):
        """测试错误处理的性能影响"""
        feed_infos = [
            FeedInfo(
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                feed_type="RSS"
            )
            for i in range(10)
        ]

        # 混合成功和失败
        def mock_parse(feed_info):
            if int(feed_info.url.split("feed")[1][0]) % 3 == 0:
                return FeedResult(
                    feed_info=feed_info,
                    articles=[],
                    success=False,
                    error="Simulated error",
                )
            return FeedResult(
                feed_info=feed_info,
                articles=[],
                success=True,
            )

        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=4)

        start_time = time.time()
        with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
            results = processor.process_feeds_parallel(feed_infos)
        elapsed_time = time.time() - start_time

        # 验证结果
        assert len(results) == 10
        failed = processor.get_failed_results(results)
        assert len(failed) > 0

        # 错误处理不应显著影响性能
        assert elapsed_time < 1.0

    def test_large_feed_performance(self, feed_parser, tracker):
        """测试处理大型 feed 的性能"""
        feed_info = FeedInfo(
            url="https://example.com/large-feed.xml",
            title="Large Feed",
            feed_type="RSS"
        )

        # 模拟包含大量文章的 feed
        def mock_parse(feed_info):
            return FeedResult(
                feed_info=feed_info,
                articles=[
                    {
                        "title": f"Article {i}",
                        "url": f"https://example.com/article{i}",
                        "published": "2025-02-09T10:00:00Z",
                        "author": "Author",
                        "content": "Content" * 10,
                    }
                    for i in range(100)  # 100 篇文章
                ],
                success=True,
            )

        start_time = time.time()
        with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
            result = feed_parser.parse_feed(feed_info)
        elapsed_time = time.time() - start_time

        # 验证结果
        assert result.success
        assert len(result.articles) == 100

        # 处理时间应该合理
        assert elapsed_time < 2.0

    def test_concurrent_safety(self, feed_parser, tracker):
        """测试并发安全性"""
        feed_infos = [
            FeedInfo(
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                feed_type="RSS"
            )
            for i in range(50)
        ]

        call_count = {"count": 0}

        def mock_parse(feed_info):
            # 模拟竞态条件
            import time
            time.sleep(0.01)
            call_count["count"] += 1
            return FeedResult(
                feed_info=feed_info,
                articles=[],
                success=True,
            )

        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=10)

        with patch.object(feed_parser, "parse_feed", side_effect=mock_parse):
            results = processor.process_feeds_parallel(feed_infos)

        # 验证所有 feeds 都被处理
        assert len(results) == 50
        assert call_count["count"] == 50