"""OPML 解析模块单元测试"""

import pytest
import requests
from unittest.mock import Mock, patch
from feedland_parser.opml_parser import OPMLParser, FeedInfo


class TestOPMLParser:
    """OPMLParser 类测试"""

    @pytest.fixture
    def opml_parser(self):
        """创建 OPMLParser 实例"""
        return OPMLParser()

    @pytest.fixture
    def sample_opml_xml(self):
        """示例 OPML XML"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Feed Subscriptions</title>
  </head>
  <body>
    <outline text="Tech News" title="Tech News" type="rss" xmlUrl="https://example.com/tech.xml"/>
    <outline text="Science" title="Science" type="atom" xmlUrl="https://example.com/science.atom"/>
    <outline text="Politics" xmlUrl="https://example.com/politics.xml"/>
  </body>
</opml>"""

    def test_parse_opml_success(self, opml_parser, sample_opml_xml):
        """测试成功解析 OPML"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = sample_opml_xml.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            feeds = opml_parser.parse_opml("https://example.com/opml.xml")

            assert len(feeds) == 3
            assert feeds[0].url == "https://example.com/tech.xml"
            assert feeds[0].title == "Tech News"
            assert feeds[0].feed_type == "RSS"

    def test_parse_opml_empty(self, opml_parser):
        """测试解析空 OPML"""
        empty_opml = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Empty</title></head>
  <body></body>
</opml>"""

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = empty_opml.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            feeds = opml_parser.parse_opml("https://example.com/opml.xml")

            assert len(feeds) == 0

    def test_parse_opml_network_error(self, opml_parser):
        """测试网络错误"""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            with pytest.raises(requests.RequestException):
                opml_parser.parse_opml("https://example.com/opml.xml")

    def test_parse_opml_invalid_xml(self, opml_parser):
        """测试无效 XML"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"invalid xml"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(Exception):
                opml_parser.parse_opml("https://example.com/opml.xml")

    def test_missing_title_uses_url(self, opml_parser):
        """测试缺少标题时使用 URL"""
        opml_no_title = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test</title></head>
  <body>
    <outline xmlUrl="https://example.com/feed.xml"/>
  </body>
</opml>"""

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = opml_no_title.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            feeds = opml_parser.parse_opml("https://example.com/opml.xml")

            assert len(feeds) == 1
            assert feeds[0].title == "https://example.com/feed.xml"

    def test_detect_feed_type_from_type_attribute(self, opml_parser):
        """测试从 type 属性检测 feed 类型"""
        # RSS
        rss_outline = Mock()
        rss_outline.get = Mock(side_effect=lambda k: {"xmlUrl": "test.xml", "type": "rss"}.get(k))
        rss_feed = opml_parser._parse_outline(rss_outline)
        assert rss_feed.feed_type == "RSS"

        # Atom
        atom_outline = Mock()
        atom_outline.get = Mock(side_effect=lambda k: {"xmlUrl": "test.atom", "type": "atom"}.get(k))
        atom_feed = opml_parser._parse_outline(atom_outline)
        assert atom_feed.feed_type == "ATOM"

    def test_detect_feed_type_from_url(self, opml_parser):
        """测试从 URL 检测 feed 类型"""
        # RSS
        rss_outline = Mock()
        rss_outline.get = Mock(side_effect=lambda k: {"xmlUrl": "https://example.com/feed.xml"}.get(k))
        rss_feed = opml_parser._parse_outline(rss_outline)
        assert rss_feed.feed_type == "RSS"

        # Atom
        atom_outline = Mock()
        atom_outline.get = Mock(side_effect=lambda k: {"xmlUrl": "https://example.com/feed.atom"}.get(k))
        atom_feed = opml_parser._parse_outline(atom_outline)
        assert atom_feed.feed_type == "ATOM"

    def test_outline_without_xmlurl_is_skipped(self, opml_parser):
        """测试跳过没有 xmlUrl 的 outline"""
        outline = Mock()
        outline.get = Mock(return_value=None)
        feed = opml_parser._parse_outline(outline)
        assert feed is None

    def test_timeout_setting(self):
        """测试超时设置"""
        parser = OPMLParser(timeout=20)
        assert parser.timeout == 20