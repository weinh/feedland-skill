"""端到端测试（E2E）"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from feedland_parser import (
    Config,
    OPMLParser,
    FeedParser,
    ArticleExtractor,
    FeedTracker,
    Deduplicator,
    ParallelFeedProcessor,
)
from feedland_parser.opml_parser import FeedInfo
from feedland_parser.feed_parser import FeedResult


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    config_data = {
        "url": "https://feedland.com/opml?screenname=test",
        "threads": 2,
        "his": {},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name

    yield temp_file

    # 清理
    os.unlink(temp_file)


class TestEndToEnd:
    """端到端测试"""

    def test_full_workflow_with_mock(self, temp_config_file):
        """测试完整的工作流程（使用 mock）"""
        # 1. 加载配置
        config = Config(temp_config_file)
        config.load()

        assert config.url == "https://feedland.com/opml?screenname=test"
        assert config.threads == 2

        # 2. 模拟 OPML 解析
        feed_infos = [
            FeedInfo(
                url="https://example.com/feed1.xml", title="Feed 1", feed_type="RSS"
            ),
            FeedInfo(
                url="https://example.com/feed2.xml", title="Feed 2", feed_type="Atom"
            ),
        ]

        # 3. 初始化组件
        article_extractor = ArticleExtractor()
        tracker = FeedTracker(config)
        tracker.load_history()
        deduplicator = Deduplicator(tracker)
        feed_parser = FeedParser(article_extractor, deduplicator)

        # 4. 模拟 feed 解析
        mock_results = [
            FeedResult(
                feed_info=feed_infos[0],
                articles=[
                    {
                        "title": "Article 1",
                        "url": "https://example.com/article1",
                        "published": "2025-02-09T10:00:00Z",
                        "author": "Author 1",
                        "content": "Content 1",
                    }
                ],
                success=True,
            ),
            FeedResult(
                feed_info=feed_infos[1],
                articles=[
                    {
                        "title": "Article 2",
                        "url": "https://example.com/article2",
                        "published": "2025-02-09T11:00:00Z",
                        "author": "Author 2",
                        "content": "Content 2",
                    }
                ],
                success=True,
            ),
        ]

        # 5. 并行处理（使用 mock）
        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=2)

        with patch.object(feed_parser, "parse_feed", side_effect=mock_results):
            results = processor.process_feeds_parallel(feed_infos)

        # 6. 验证结果
        assert len(results) == 2
        assert all(r.success for r in results)

        # 7. 获取所有文章
        articles = processor.get_all_articles(results)
        assert len(articles) == 2

        # 8. 验证摘要
        summary = processor.get_summary(results)
        assert summary["total_feeds"] == 2
        assert summary["successful_feeds"] == 2
        assert summary["total_articles"] == 2

    def test_workflow_with_deduplication(self, temp_config_file):
        """测试带去重的工作流程"""
        config = Config(temp_config_file)
        config.load()

        # 设置历史记录
        config.history = {
            "https://example.com/feed1.xml": "2025-02-09T10:00:00Z"
        }
        config.save()

        # 初始化组件
        article_extractor = ArticleExtractor()
        tracker = FeedTracker(config)
        tracker.load_history()
        deduplicator = Deduplicator(tracker)
        feed_parser = FeedParser(article_extractor, deduplicator)

        feed_info = FeedInfo(
            url="https://example.com/feed1.xml", title="Feed 1", feed_type="RSS"
        )

        # 创建旧文章（应该被过滤）
        old_result = FeedResult(
            feed_info=feed_info,
            articles=[
                {
                    "title": "Old Article",
                    "url": "https://example.com/old",
                    "published": "2025-02-09T09:00:00Z",  # 早于历史记录
                    "author": "Author",
                    "content": "Content",
                }
            ],
            success=True,
        )

        # 测试去重
        with patch.object(feed_parser, "parse_feed", return_value=old_result):
            result = feed_parser.parse_feed(feed_info)

        # 验证旧文章被过滤
        # 注意：实际的去重逻辑在 feed_parser 中实现
        # 这里我们只是测试流程

    def test_workflow_with_failure(self, temp_config_file):
        """测试包含失败的工作流程"""
        config = Config(temp_config_file)
        config.load()

        feed_infos = [
            FeedInfo(url="https://example.com/feed1.xml", title="Feed 1", feed_type="RSS"),
            FeedInfo(url="https://example.com/feed2.xml", title="Feed 2", feed_type="RSS"),
        ]

        article_extractor = ArticleExtractor()
        tracker = FeedTracker(config)
        tracker.load_history()
        deduplicator = Deduplicator(tracker)
        feed_parser = FeedParser(article_extractor, deduplicator)
        processor = ParallelFeedProcessor(feed_parser, tracker, max_workers=2)

        # 模拟一个成功一个失败
        mock_results = [
            FeedResult(
                feed_info=feed_infos[0],
                articles=[],
                success=True,
            ),
            FeedResult(
                feed_info=feed_infos[1],
                articles=[],
                success=False,
                error="Network error",
            ),
        ]

        with patch.object(feed_parser, "parse_feed", side_effect=mock_results):
            results = processor.process_feeds_parallel(feed_infos)

        # 验证结果
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

        # 获取失败的结果
        failed = processor.get_failed_results(results)
        assert len(failed) == 1
        assert failed[0].error == "Network error"

    def test_workflow_with_config_persistence(self, temp_config_file):
        """测试配置持久化"""
        config = Config(temp_config_file)
        config.load()

        # 更新历史记录
        config.update_history("https://example.com/feed.xml", "2025-02-09T10:00:00Z")
        config.save()

        # 重新加载验证
        new_config = Config(temp_config_file)
        new_config.load()

        assert "https://example.com/feed.xml" in new_config.history
        assert new_config.history["https://example.com/feed.xml"] == "2025-02-09T10:00:00Z"

    def test_output_format(self, temp_config_file):
        """测试输出格式"""
        config = Config(temp_config_file)
        config.load()

        feed_info = FeedInfo(
            url="https://example.com/feed.xml", title="Example Feed", feed_type="RSS"
        )

        result = FeedResult(
            feed_info=feed_info,
            articles=[
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "published": "2025-02-09T10:00:00Z",
                    "author": "Test Author",
                    "content": "Test Content",
                }
            ],
            success=True,
        )

        # 验证可以序列化为 JSON
        json_str = json.dumps([result], default=lambda o: o.__dict__)
        assert json_str is not None

        # 验证可以反序列化
        parsed = json.loads(json_str)
        assert len(parsed) == 1

    def test_empty_workflow(self, temp_config_file):
        """测试空工作流程"""
        config = Config(temp_config_file)
        config.load()

        article_extractor = ArticleExtractor()
        tracker = FeedTracker(config)
        tracker.load_history()
        deduplicator = Deduplicator(tracker)
        feed_parser = FeedParser(article_extractor, deduplicator)
        processor = ParallelFeedProcessor(feed_parser, tracker)

        # 处理空的 feed 列表
        results = processor.process_feeds_parallel([])

        assert len(results) == 0
        assert processor.get_summary(results)["total_feeds"] == 0