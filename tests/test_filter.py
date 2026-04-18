"""Filter 模块单元测试"""

import pytest
import tempfile
import json
import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

from feedland_parser.filter import Filter
from feedland_parser.config import Config


class TestFilter:
    """Filter 类测试"""

    @pytest.fixture
    def config(self):
        """创建配置对象"""
        config_data = {
            "url": "https://test.com/opml",
            "his": {
                "https://example.com/feed1.xml": "2025-02-09T10:00:00Z",
                "https://example.com/feed2.xml": "2025-02-09T09:00:00Z",
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        config = Config(temp_file)
        config.load()

        yield config

        import os
        os.unlink(temp_file)

    @pytest.fixture
    def filter_obj(self, config):
        """创建 Filter 对象"""
        return Filter(config)

    def test_init(self, config):
        """测试初始化"""
        filter_obj = Filter(config)
        assert filter_obj.config == config
        assert filter_obj._history == {}
        assert hasattr(filter_obj, '_lock')

    def test_load_history(self, filter_obj):
        """测试加载历史记录"""
        history = filter_obj.load_history()
        assert "https://example.com/feed1.xml" in history
        assert "https://example.com/feed2.xml" in history
        assert len(history) == 2

    def test_load_history_empty(self, config):
        """测试加载空历史记录"""
        config.his = {}
        filter_obj = Filter(config)
        history = filter_obj.load_history()
        assert history == {}

    def test_save_history(self, filter_obj):
        """测试保存历史记录"""
        filter_obj.load_history()
        filter_obj.update_timestamp("https://new-feed.com/feed.xml", "2025-02-10T12:00:00Z")
        filter_obj.save_history()

        # 重新加载验证
        new_filter = Filter(filter_obj.config)
        new_filter.load_history()
        assert "https://new-feed.com/feed.xml" in new_filter._history
        assert new_filter._history["https://new-feed.com/feed.xml"] == "2025-02-10T12:00:00Z"

    def test_get_last_timestamp(self, filter_obj):
        """测试获取最后时间戳"""
        filter_obj.load_history()
        timestamp = filter_obj.get_last_timestamp("https://example.com/feed1.xml")
        assert timestamp == "2025-02-09T10:00:00Z"

    def test_get_last_timestamp_not_found(self, filter_obj):
        """测试获取不存在的 feed 时间戳"""
        filter_obj.load_history()
        timestamp = filter_obj.get_last_timestamp("https://not-exist.com/feed.xml")
        assert timestamp is None

    def test_update_timestamp(self, filter_obj):
        """测试更新时间戳"""
        filter_obj.update_timestamp("https://test.com/feed.xml", "2025-02-10T12:00:00Z")
        assert filter_obj._history["https://test.com/feed.xml"] == "2025-02-10T12:00:00Z"

    def test_is_newer_than_last(self, filter_obj):
        """测试检查文章是否比记录的时间戳更新"""
        filter_obj.load_history()

        # 更新的文章
        is_newer = filter_obj.is_newer_than_last(
            "https://example.com/feed1.xml",
            "2025-02-09T11:00:00Z"
        )
        assert is_newer is True

        # 旧的文章
        is_newer = filter_obj.is_newer_than_last(
            "https://example.com/feed1.xml",
            "2025-02-09T09:00:00Z"
        )
        assert is_newer is False

        # 相同时间的文章
        is_newer = filter_obj.is_newer_than_last(
            "https://example.com/feed1.xml",
            "2025-02-09T10:00:00Z"
        )
        assert is_newer is False

    def test_is_newer_than_last_no_record(self, filter_obj):
        """测试检查没有记录的 feed"""
        is_newer = filter_obj.is_newer_than_last(
            "https://not-exist.com/feed.xml",
            "2025-02-09T10:00:00Z"
        )
        assert is_newer is True

    def test_is_newer_than_last_invalid_timestamp(self, filter_obj):
        """测试无效时间戳"""
        is_newer = filter_obj.is_newer_than_last(
            "https://example.com/feed1.xml",
            "invalid-timestamp"
        )
        assert is_newer is True  # 解析失败时默认返回 True

    def test_get_feed_count(self, filter_obj):
        """测试获取 feed 数量"""
        filter_obj.load_history()
        count = filter_obj.get_feed_count()
        assert count == 2

        filter_obj.update_timestamp("https://new.com/feed.xml", "2025-02-10T12:00:00Z")
        count = filter_obj.get_feed_count()
        assert count == 3

    def test_remove_feed(self, filter_obj):
        """测试移除 feed 记录"""
        filter_obj.load_history()
        filter_obj.remove_feed("https://example.com/feed1.xml")
        assert "https://example.com/feed1.xml" not in filter_obj._history
        assert filter_obj.get_feed_count() == 1

    def test_remove_feed_not_exist(self, filter_obj):
        """测试移除不存在的 feed"""
        filter_obj.load_history()
        filter_obj.remove_feed("https://not-exist.com/feed.xml")
        assert filter_obj.get_feed_count() == 2

    def test_clear_history(self, filter_obj):
        """测试清空历史记录"""
        filter_obj.load_history()
        filter_obj.clear_history()
        assert filter_obj.get_feed_count() == 0
        assert filter_obj._history == {}

    def test_is_new_article(self, filter_obj):
        """测试检查文章是否是新文章"""
        filter_obj.load_history()

        # 新文章
        is_new = filter_obj.is_new_article(
            "https://example.com/feed1.xml",
            "https://example.com/article/new",
            "2025-02-09T11:00:00Z"
        )
        assert is_new is True

        # 旧文章
        is_new = filter_obj.is_new_article(
            "https://example.com/feed1.xml",
            "https://example.com/article/old",
            "2025-02-09T09:00:00Z"
        )
        assert is_new is False

    def test_is_new_article_no_record(self, filter_obj):
        """测试没有记录的 feed"""
        is_new = filter_obj.is_new_article(
            "https://not-exist.com/feed.xml",
            "https://not-exist.com/article",
            "2025-02-09T10:00:00Z"
        )
        assert is_new is True

    def test_filter_articles(self, filter_obj):
        """测试过滤文章"""
        filter_obj.load_history()

        articles = [
            {
                "url": "https://example.com/article1",
                "title": "New Article",
                "published": "2025-02-09T11:00:00Z"
            },
            {
                "url": "https://example.com/article2",
                "title": "Old Article",
                "published": "2025-02-09T09:00:00Z"
            },
            {
                "url": "https://example.com/article3",
                "title": "No Timestamp",
            },
            {
                "url": "https://example.com/article4",
                "title": "Same Time",
                "published": "2025-02-09T10:00:00Z"
            }
        ]

        filtered = filter_obj.filter_articles("https://example.com/feed1.xml", articles)

        # 应该保留新文章和没有时间戳的文章
        assert len(filtered) == 2
        assert any(a["url"] == "https://example.com/article1" for a in filtered)
        assert any(a["url"] == "https://example.com/article3" for a in filtered)

    def test_should_skip_article(self, filter_obj):
        """测试判断是否应该跳过文章"""
        filter_obj.load_history()

        # 不应该跳过新文章
        should_skip = filter_obj.should_skip_article(
            "https://example.com/feed1.xml",
            "https://example.com/article/new",
            "2025-02-09T11:00:00Z"
        )
        assert should_skip is False

        # 应该跳过旧文章
        should_skip = filter_obj.should_skip_article(
            "https://example.com/feed1.xml",
            "https://example.com/article/old",
            "2025-02-09T09:00:00Z"
        )
        assert should_skip is True

    def test_concurrent_update(self, filter_obj):
        """测试并发更新时间戳"""
        threads = []
        errors = []

        def update_feed(feed_num):
            try:
                for i in range(10):
                    feed_url = f"https://test{feed_num}.com/feed.xml"
                    timestamp = f"2025-02-10T{10 + i}:00:00Z"
                    filter_obj.update_timestamp(feed_url, timestamp)
            except Exception as e:
                errors.append(e)

        for i in range(5):
            t = threading.Thread(target=update_feed, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert filter_obj.get_feed_count() == 5

    def test_filter_articles_empty_list(self, filter_obj):
        """测试过滤空文章列表"""
        filtered = filter_obj.filter_articles("https://example.com/feed.xml", [])
        assert filtered == []

    def test_save_history_error(self, filter_obj):
        """测试保存历史记录时的错误处理"""
        with patch.object(filter_obj.config, 'save', side_effect=Exception("Save error")):
            with pytest.raises(Exception):
                filter_obj.save_history()

    def test_load_history_error(self, config):
        """测试加载历史记录时的错误处理"""
        config.his = None
        filter_obj = Filter(config)
        history = filter_obj.load_history()
        assert history == {}

    def test_update_timestamp_concurrent(self, filter_obj):
        """测试并发更新时间戳的线程安全性"""
        results = []

        def update_with_delay(feed_url, timestamp, delay):
            import time
            time.sleep(delay)
            filter_obj.update_timestamp(feed_url, timestamp)
            results.append((feed_url, timestamp))

        threads = [
            threading.Thread(target=update_with_delay, args=("feed1", "2025-02-10T10:00:00Z", 0.1)),
            threading.Thread(target=update_with_delay, args=("feed1", "2025-02-10T11:00:00Z", 0.2)),
            threading.Thread(target=update_with_delay, args=("feed2", "2025-02-10T12:00:00Z", 0.15)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证所有操作都完成
        assert len(results) == 3
        # 验证最终值
        assert filter_obj._history["feed1"] == "2025-02-10T11:00:00Z"  # 最后更新的值
        assert filter_obj._history["feed2"] == "2025-02-10T12:00:00Z"