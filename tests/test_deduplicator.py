"""去重逻辑模块单元测试"""

import pytest
from unittest.mock import MagicMock
from feedland_parser.deduplicator import Deduplicator
from feedland_parser.tracker import FeedTracker


class TestDeduplicator:
    """Deduplicator 类测试"""

    @pytest.fixture
    def tracker(self):
        """创建 FeedTracker 实例"""
        return MagicMock(spec=FeedTracker)

    @pytest.fixture
    def deduplicator(self, tracker):
        """创建 Deduplicator 实例"""
        return Deduplicator(tracker)

    def test_is_new_article_true(self, deduplicator, tracker):
        """测试检查新文章"""
        tracker.is_newer_than_last.return_value = True

        result = deduplicator.is_new_article(
            "https://example.com/feed.xml",
            "https://example.com/article1",
            "2025-02-09T10:00:00Z"
        )

        assert result is True

    def test_is_new_article_false(self, deduplicator, tracker):
        """测试检查旧文章"""
        tracker.is_newer_than_last.return_value = False

        result = deduplicator.is_new_article(
            "https://example.com/feed.xml",
            "https://example.com/article1",
            "2025-02-09T10:00:00Z"
        )

        assert result is False

    def test_is_new_article_error_handling(self, deduplicator, tracker):
        """测试错误处理"""
        tracker.is_newer_than_last.side_effect = Exception("Test error")

        result = deduplicator.is_new_article(
            "https://example.com/feed.xml",
            "https://example.com/article1",
            "2025-02-09T10:00:00Z"
        )

        # 出错时认为是新文章
        assert result is True

    def test_normalize_url_remove_tracking_params(self, deduplicator):
        """测试移除跟踪参数"""
        url = "https://example.com/article?utm_source=google&utm_medium=cpc&utm_campaign=test"

        normalized = deduplicator.normalize_url(url)

        assert "utm_source" not in normalized
        assert "utm_medium" not in normalized
        assert "utm_campaign" not in normalized

    def test_normalize_url_preserve_other_params(self, deduplicator):
        """测试保留其他参数"""
        url = "https://example.com/article?page=1&sort=date"

        normalized = deduplicator.normalize_url(url)

        assert "page=1" in normalized
        assert "sort=date" in normalized

    def test_normalize_url_no_params(self, deduplicator):
        """测试没有参数的 URL"""
        url = "https://example.com/article"

        normalized = deduplicator.normalize_url(url)

        assert normalized == url

    def test_normalize_url_invalid(self, deduplicator):
        """测试无效 URL"""
        url = "invalid-url"

        normalized = deduplicator.normalize_url(url)

        # 无效 URL 返回原值
        assert normalized == url

    def test_filter_articles_by_timestamp(self, deduplicator, tracker):
        """测试根据时间戳过滤文章"""
        tracker.is_newer_than_last.side_effect = lambda f, t: t > "2025-02-09T10:00:00Z"

        articles = [
            {"url": "https://example.com/article1", "published": "2025-02-09T09:00:00Z"},
            {"url": "https://example.com/article2", "published": "2025-02-09T11:00:00Z"},
            {"url": "https://example.com/article3", "published": "2025-02-09T12:00:00Z"},
        ]

        filtered = deduplicator.filter_articles_by_timestamp(
            "https://example.com/feed.xml",
            articles
        )

        assert len(filtered) == 2  # article2 和 article3

    def test_filter_articles_missing_timestamp(self, deduplicator):
        """测试缺少时间戳的文章"""
        articles = [
            {"url": "https://example.com/article1", "published": "2025-02-09T10:00:00Z"},
            {"url": "https://example.com/article2"},  # 缺少时间戳
        ]

        filtered = deduplicator.filter_articles_by_timestamp(
            "https://example.com/feed.xml",
            articles
        )

        # 缺少时间戳的文章应该被保留
        assert len(filtered) == 2

    def test_filter_articles_error_handling(self, deduplicator, tracker):
        """测试过滤时的错误处理"""
        tracker.is_newer_than_last.side_effect = Exception("Test error")

        articles = [
            {"url": "https://example.com/article1", "published": "2025-02-09T10:00:00Z"},
        ]

        filtered = deduplicator.filter_articles_by_timestamp(
            "https://example.com/feed.xml",
            articles
        )

        # 出错时保留文章
        assert len(filtered) == 1

    def test_should_skip_article_true(self, deduplicator, tracker):
        """测试应该跳过文章"""
        tracker.is_newer_than_last.return_value = False

        should_skip = deduplicator.should_skip_article(
            "https://example.com/feed.xml",
            "https://example.com/article1",
            "2025-02-09T10:00:00Z"
        )

        assert should_skip is True

    def test_should_skip_article_false(self, deduplicator, tracker):
        """测试不应该跳过文章"""
        tracker.is_newer_than_last.return_value = True

        should_skip = deduplicator.should_skip_article(
            "https://example.com/feed.xml",
            "https://example.com/article1",
            "2025-02-09T10:00:00Z"
        )

        assert should_skip is False