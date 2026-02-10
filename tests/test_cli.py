"""CLI 集成测试"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from feedland_parser.cli import parse_arguments, setup_logging, generate_output
from feedland_parser.opml_parser import FeedInfo
from feedland_parser.feed_parser import FeedResult


class TestCLI:
    """CLI 函数测试"""

    def test_parse_arguments_default(self):
        """测试默认参数解析"""
        with patch('sys.argv', ['yonglelaoren-feedland-parser']):
            args = parse_arguments()
            assert args.config is None
            assert args.verbose is False
            assert args.quiet is False

    def test_parse_arguments_with_config(self):
        """测试带配置文件路径的参数解析"""
        with patch('sys.argv', ['yonglelaoren-feedland-parser', '--config', './config.json']):
            args = parse_arguments()
            assert args.config == './config.json'

    def test_parse_arguments_with_verbose(self):
        """测试 verbose 参数解析"""
        with patch('sys.argv', ['yonglelaoren-feedland-parser', '--verbose']):
            args = parse_arguments()
            assert args.verbose is True

    def test_parse_arguments_with_quiet(self):
        """测试 quiet 参数解析"""
        with patch('sys.argv', ['yonglelaoren-feedland-parser', '--quiet']):
            args = parse_arguments()
            assert args.quiet is True

    def test_parse_arguments_with_version(self, capsys):
        """测试 version 参数解析"""
        with patch('sys.argv', ['yonglelaoren-feedland-parser', '--version']):
            with pytest.raises(SystemExit):
                parse_arguments()
        captured = capsys.readouterr()
        assert '0.1.0' in captured.out

    def test_setup_logging_verbose(self):
        """测试 verbose 日志设置"""
        setup_logging(verbose=True, quiet=False)
        import logging
        assert logging.getLogger().level == logging.DEBUG

    def test_setup_logging_quiet(self):
        """测试 quiet 日志设置"""
        setup_logging(verbose=False, quiet=True)
        import logging
        assert logging.getLogger().level == logging.ERROR

    def test_setup_logging_default(self):
        """测试默认日志设置"""
        setup_logging(verbose=False, quiet=False)
        import logging
        assert logging.getLogger().level == logging.INFO

    def test_generate_output_empty(self):
        """测试生成空输出"""
        results = []
        output = generate_output(results)
        assert output == []

    def test_generate_output_with_success(self):
        """测试生成成功输出"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Example Feed",
            feed_type="RSS"
        )
        result = FeedResult(
            feed_info=feed_info,
            articles=[
                {
                    "title": "Article 1",
                    "url": "https://example.com/article1",
                    "published": "2025-02-09T10:00:00Z",
                    "author": "Author",
                    "content": "Content",
                }
            ],
            success=True
        )

        output = generate_output([result])

        assert len(output) == 1
        assert output[0]["feed_url"] == "https://example.com/feed.xml"
        assert output[0]["feed_title"] == "Example Feed"
        assert len(output[0]["articles"]) == 1

    def test_generate_output_with_failure(self):
        """测试生成失败输出"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Example Feed",
            feed_type="RSS"
        )
        result = FeedResult(
            feed_info=feed_info,
            articles=[],
            success=False,
            error="Network error"
        )

        output = generate_output([result])

        assert len(output) == 0  # 失败的结果不应包含在输出中

    def test_generate_output_mixed(self):
        """测试生成混合输出"""
        feed_info1 = FeedInfo(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            feed_type="RSS"
        )
        feed_info2 = FeedInfo(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            feed_type="Atom"
        )

        results = [
            FeedResult(
                feed_info=feed_info1,
                articles=[
                    {
                        "title": "Article 1",
                        "url": "https://example.com/article1",
                        "published": "2025-02-09T10:00:00Z",
                    }
                ],
                success=True
            ),
            FeedResult(
                feed_info=feed_info2,
                articles=[],
                success=False,
                error="Error"
            ),
        ]

        output = generate_output(results)

        assert len(output) == 1
        assert output[0]["feed_title"] == "Feed 1"

    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        config_data = {
            "url": "https://feedland.com/opml?screenname=test",
            "threads": 2,
            "his": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        yield temp_file

        # 清理
        os.unlink(temp_file)

    def test_main_with_config(self, temp_config_file):
        """测试使用配置文件的主函数"""
        # 由于主函数涉及网络请求，这里只测试配置加载部分
        from feedland_parser.cli import Config

        config = Config(temp_config_file)
        config.load()

        assert config.url == "https://feedland.com/opml?screenname=test"
        assert config.threads == 2

    def test_generate_output_json_serializable(self):
        """测试输出是否可以序列化为 JSON"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Example Feed",
            feed_type="RSS"
        )
        result = FeedResult(
            feed_info=feed_info,
            articles=[
                {
                    "title": "Article 1",
                    "url": "https://example.com/article1",
                    "published": "2025-02-09T10:00:00Z",
                    "author": "Author",
                    "content": "Content",
                }
            ],
            success=True
        )

        output = generate_output([result])

        # 确保可以序列化为 JSON
        json_str = json.dumps(output)
        assert json_str is not None

        # 确保可以反序列化
        parsed = json.loads(json_str)
        assert len(parsed) == 1