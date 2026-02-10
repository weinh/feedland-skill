"""时间戳跟踪模块单元测试"""

import json
import pytest
from unittest.mock import MagicMock
from feedland_parser.tracker import FeedTracker
from feedland_parser.config import Config


class TestFeedTracker:
    """FeedTracker 类测试"""

    @pytest.fixture
    def config(self, tmp_path):
        """创建测试配置"""
        config_path = tmp_path / "config.json"
        config_data = {"url": "test", "his": {}}
        config_path.write_text(json.dumps(config_data))
        return Config(str(config_path))

    @pytest.fixture
    def tracker(self, config):
        """创建 FeedTracker 实例"""
        return FeedTracker(config)

    def test_load_history_empty(self, tracker):
        """测试加载空历史记录"""
        history = tracker.load_history()
        assert history == {}

    def test_load_history_with_data(self, tracker):
        """测试加载包含数据的历史记录"""
        tracker._history = {
            "feed1": "2025-02-09T10:00:00Z",
            "feed2": "2025-02-09T11:00:00Z",
        }

        history = tracker.load_history()
        assert len(history) == 2
        assert history["feed1"] == "2025-02-09T10:00:00Z"

    def test_get_last_timestamp(self, tracker):
        """测试获取最后时间戳"""
        tracker._history = {"feed1": "2025-02-09T10:00:00Z"}

        timestamp = tracker.get_last_timestamp("feed1")
        assert timestamp == "2025-02-09T10:00:00Z"

    def test_get_last_timestamp_not_exists(self, tracker):
        """测试获取不存在的 feed 时间戳"""
        timestamp = tracker.get_last_timestamp("nonexistent")
        assert timestamp is None

    def test_update_timestamp(self, tracker):
        """测试更新时间戳"""
        tracker.update_timestamp("feed1", "2025-02-09T10:00:00Z")

        assert tracker._history["feed1"] == "2025-02-09T10:00:00Z"

    def test_is_newer_than_last_no_history(self, tracker):
        """测试没有历史记录时的比较"""
        result = tracker.is_newer_than_last("feed1", "2025-02-09T10:00:00Z")
        assert result is True

    def test_is_newer_than_last_newer(self, tracker):
        """测试文章比记录更新"""
        tracker._history = {"feed1": "2025-02-09T09:00:00Z"}

        result = tracker.is_newer_than_last("feed1", "2025-02-09T10:00:00Z")
        assert result is True

    def test_is_newer_than_last_older(self, tracker):
        """测试文章比记录更旧"""
        tracker._history = {"feed1": "2025-02-09T11:00:00Z"}

        result = tracker.is_newer_than_last("feed1", "2025-02-09T10:00:00Z")
        assert result is False

    def test_is_newer_than_last_invalid_timestamp(self, tracker):
        """测试无效时间戳"""
        tracker._history = {"feed1": "2025-02-09T10:00:00Z"}

        result = tracker.is_newer_than_last("feed1", "invalid")
        assert result is True  # 保守起见认为是新文章

    def test_get_feed_count(self, tracker):
        """测试获取 feed 数量"""
        tracker._history = {
            "feed1": "2025-02-09T10:00:00Z",
            "feed2": "2025-02-09T11:00:00Z",
            "feed3": "2025-02-09T12:00:00Z",
        }

        count = tracker.get_feed_count()
        assert count == 3

    def test_remove_feed(self, tracker):
        """测试移除 feed"""
        tracker._history = {
            "feed1": "2025-02-09T10:00:00Z",
            "feed2": "2025-02-09T11:00:00Z",
        }

        tracker.remove_feed("feed1")

        assert "feed1" not in tracker._history
        assert tracker.get_feed_count() == 1

    def test_clear_history(self, tracker):
        """测试清空历史记录"""
        tracker._history = {
            "feed1": "2025-02-09T10:00:00Z",
            "feed2": "2025-02-09T11:00:00Z",
        }

        tracker.clear_history()

        assert tracker.get_feed_count() == 0

    def test_save_history(self, tracker, config):
        """测试保存历史记录"""
        tracker._history = {"feed1": "2025-02-09T10:00:00Z"}
        tracker.save_history()

        # 重新加载验证
        config.load()
        assert config.his["feed1"] == "2025-02-09T10:00:00Z"