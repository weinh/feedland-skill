"""配置模块单元测试"""

import json
import os
import tempfile
import pytest
from feedland_parser.config import Config


class TestConfig:
    """Config 类测试"""

    def test_find_config_file_current_directory(self, tmp_path):
        """测试从当前目录查找配置文件"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test"}')

        config = Config(str(config_path))
        assert config.config_path == str(config_path)

    def test_load_valid_config(self, tmp_path):
        """测试加载有效配置"""
        config_path = tmp_path / "config.json"
        config_data = {"url": "https://test.com/opml", "threads": 5, "his": {}}
        config_path.write_text(json.dumps(config_data))

        config = Config(str(config_path))
        loaded_config = config.load()

        assert loaded_config == config_data

    def test_load_invalid_json(self, tmp_path):
        """测试加载无效 JSON"""
        config_path = tmp_path / "config.json"
        config_path.write_text("invalid json")

        config = Config(str(config_path))
        with pytest.raises(json.JSONDecodeError):
            config.load()

    def test_threads_default_value(self, tmp_path):
        """测试线程数默认值"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test"}')

        config = Config(str(config_path))
        config.load()

        assert config.threads > 0

    def test_threads_custom_value(self, tmp_path):
        """测试自定义线程数"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test", "threads": 15}')

        config = Config(str(config_path))
        config.load()

        assert config.threads == 15

    def test_threads_invalid_value(self, tmp_path):
        """测试无效线程数"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test", "threads": "invalid"}')

        config = Config(str(config_path))
        config.load()

        assert config.threads > 0  # 应该使用默认值

    def test_his_property(self, tmp_path):
        """测试历史记录属性"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test", "his": {"feed1": "2025-02-09T10:00:00Z"}}')

        config = Config(str(config_path))
        config.load()

        assert config.his == {"feed1": "2025-02-09T10:00:00Z"}

    def test_update_history(self, tmp_path):
        """测试更新历史记录"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test"}')

        config = Config(str(config_path))
        config.load()
        config.update_history("feed1", "2025-02-09T10:00:00Z")
        config.save()

        # 重新加载验证
        config2 = Config(str(config_path))
        config2.load()
        assert config2.his["feed1"] == "2025-02-09T10:00:00Z"

    def test_validate_valid_config(self, tmp_path):
        """测试验证有效配置"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test"}')

        config = Config(str(config_path))
        config.load()

        assert config.validate() is True

    def test_validate_missing_url(self, tmp_path):
        """测试验证缺少 URL 的配置"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{}')

        config = Config(str(config_path))
        config.load()

        assert config.validate() is False

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"url": "test"}')

        config = Config(str(config_path))
        config.load()
        config.url = "https://new-url.com/opml"
        config.threads = 20
        config.save()

        # 重新加载验证
        config2 = Config(str(config_path))
        config2.load()
        assert config2.url == "https://new-url.com/opml"
        assert config2.threads == 20