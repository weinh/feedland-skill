"""并行处理模块集成测试"""

import pytest
from unittest.mock import MagicMock, patch, call
from feedland_parser.parallel_processor import ParallelFeedProcessor
from feedland_parser.feed_parser import FeedParser, FeedResult
from feedland_parser.tracker import FeedTracker
from feedland_parser.opml_parser import FeedInfo


class TestParallelFeedProcessor:
    """ParallelFeedProcessor 类测试"""

    @pytest.fixture
    def feed_parser(self):
        """创建 FeedParser 实例"""
        return MagicMock(spec=FeedParser)

    @pytest.fixture
    def tracker(self):
        """创建 FeedTracker 实例"""
        tracker = MagicMock(spec=FeedTracker)
        tracker._history = {}
        return tracker

    @pytest.fixture
    def processor(self, feed_parser, tracker):
        """创建 ParallelFeedProcessor 实例"""
        return ParallelFeedProcessor(
            feed_parser=feed_parser,
            tracker=tracker,
            max_workers=2
        )

    def test_process_feeds_parallel_success(self, processor, feed_parser, tracker):
        """测试成功并行处理多个 feeds"""
        feed_infos = [
            FeedInfo(url=f"https://example.com/feed{i}.xml", title=f"Feed {i}", feed_type="RSS")
            for i in range(3)
        ]

        # 模拟成功的解析结果
        feed_parser.parse_feed.side_effect = [
            FeedResult(
                feed_info=feed_infos[0],
                articles=[
                    {
                        "title": f"Article {0}",
                        "url": f"https://example.com/article{0}",
                        "published": "2025-02-09T10:00:00Z",
                        "author": "Author",
                        "content": "Content",
                    }
                ],
                success=True
            ),
            FeedResult(
                feed_info=feed_infos[1],
                articles=[
                    {
                        "title": f"Article {1}",
                        "url": f"https://example.com/article{1}",
                        "published": "2025-02-09T11:00:00Z",
                        "author": "Author",
                        "content": "Content",
                    }
                ],
                success=True
            ),
            FeedResult(
                feed_info=feed_infos[2],
                articles=[],
                success=True
            ),
        ]

        results = processor.process_feeds_parallel(feed_infos)

        assert len(results) == 3
        assert all(r.success for r in results)

        # 验证 tracker 被更新
        assert tracker.update_timestamp.call_count == 2  # 只有两个 feed 有文章

    def test_process_feeds_parallel_with_failure(self, processor, feed_parser):
        """测试并行处理中包含失败的 feeds"""
        feed_infos = [
            FeedInfo(url="https://example.com/feed1.xml", title="Feed 1", feed_type="RSS"),
            FeedInfo(url="https://example.com/feed2.xml", title="Feed 2", feed_type="RSS"),
        ]

        # 模拟一个成功一个失败
        feed_parser.parse_feed.side_effect = [
            FeedResult(
                feed_info=feed_infos[0],
                articles=[],
                success=True
            ),
            FeedResult(
                feed_info=feed_infos[1],
                articles=[],
                success=False,
                error="Network error"
            ),
        ]

        results = processor.process_feeds_parallel(feed_infos)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    def test_progress_callback(self, processor, feed_parser):
        """测试进度回调"""
        feed_infos = [
            FeedInfo(url="https://example.com/feed1.xml", title="Feed 1", feed_type="RSS"),
            FeedInfo(url="https://example.com/feed2.xml", title="Feed 2", feed_type="RSS"),
        ]

        feed_parser.parse_feed.side_effect = [
            FeedResult(feed_info=feed_infos[0], articles=[], success=True),
            FeedResult(feed_info=feed_infos[1], articles=[], success=True),
        ]

        progress_calls = []

        def callback(current, total, result):
            progress_calls.append((current, total, result))

        processor.process_feeds_parallel(feed_infos, progress_callback=callback)

        assert len(progress_calls) == 2
        assert progress_calls[0][0] == 1  # 第一个完成
        assert progress_calls[1][0] == 2  # 第二个完成

    def test_get_successful_results(self, processor):
        """测试获取成功的结果"""
        results = [
            FeedResult(
                feed_info=FeedInfo(url="feed1", title="Feed 1", feed_type="RSS"),
                articles=[],
                success=True
            ),
            FeedResult(
                feed_info=FeedInfo(url="feed2", title="Feed 2", feed_type="RSS"),
                articles=[],
                success=False,
                error="Error"
            ),
        ]

        successful = processor.get_successful_results(results)

        assert len(successful) == 1
        assert successful[0].success is True

    def test_get_failed_results(self, processor):
        """测试获取失败的结果"""
        results = [
            FeedResult(
                feed_info=FeedInfo(url="feed1", title="Feed 1", feed_type="RSS"),
                articles=[],
                success=True
            ),
            FeedResult(
                feed_info=FeedInfo(url="feed2", title="Feed 2", feed_type="RSS"),
                articles=[],
                success=False,
                error="Error"
            ),
        ]

        failed = processor.get_failed_results(results)

        assert len(failed) == 1
        assert failed[0].success is False

    def test_get_all_articles(self, processor):
        """测试获取所有文章"""
        results = [
            FeedResult(
                feed_info=FeedInfo(url="feed1", title="Feed 1", feed_type="RSS"),
                articles=[
                    {"title": "Article 1", "url": "url1", "content": "content1"},
                    {"title": "Article 2", "url": "url2", "content": "content2"},
                ],
                success=True
            ),
            FeedResult(
                feed_info=FeedInfo(url="feed2", title="Feed 2", feed_type="RSS"),
                articles=[
                    {"title": "Article 3", "url": "url3", "content": "content3"},
                ],
                success=True
            ),
            FeedResult(
                feed_info=FeedInfo(url="feed3", title="Feed 3", feed_type="RSS"),
                articles=[],
                success=False
            ),
        ]

        articles = processor.get_all_articles(results)

        assert len(articles) == 3

    def test_get_summary(self, processor):
        """测试获取摘要"""
        results = [
            FeedResult(
                feed_info=FeedInfo(url="feed1", title="Feed 1", feed_type="RSS"),
                articles=[{"title": "Article 1"}],
                success=True
            ),
            FeedResult(
                feed_info=FeedInfo(url="feed2", title="Feed 2", feed_type="RSS"),
                articles=[],
                success=False,
                error="Error"
            ),
        ]

        summary = processor.get_summary(results)

        assert summary["total_feeds"] == 2
        assert summary["successful_feeds"] == 1
        assert summary["failed_feeds"] == 1
        assert summary["total_articles"] == 1
        assert "feed2" in summary["failed_feeds_list"]

    def test_max_workers_setting(self):
        """测试最大工作线程数设置"""
        feed_parser = MagicMock(spec=FeedParser)
        tracker = MagicMock(spec=FeedTracker)

        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=5)
        assert processor.max_workers == 5

    def test_thread_safety(self, processor, feed_parser, tracker):
        """测试线程安全性"""
        # 创建多个 feeds
        feed_infos = [
            FeedInfo(url=f"https://example.com/feed{i}.xml", title=f"Feed {i}", feed_type="RSS")
            for i in range(10)
        ]

        # 模拟所有成功
        feed_parser.parse_feed.side_effect = [
            FeedResult(
                feed_info=feed_info,
                articles=[
                    {
                        "title": f"Article {i}",
                        "url": f"https://example.com/article{i}",
                        "published": f"2025-02-09T{10 + i}:00:00Z",
                        "author": "Author",
                        "content": "Content",
                    }
                ],
                success=True
            )
            for feed_info in feed_infos
        ]

        results = processor.process_feeds_parallel(feed_infos)

        assert len(results) == 10
        assert all(r.success for r in results)

        # 验证所有 feeds 都被更新到 tracker
        assert tracker.update_timestamp.call_count == 10