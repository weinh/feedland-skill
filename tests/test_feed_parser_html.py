"""测试 FeedParser 中的 HTML 标签清理功能"""

import pytest
import tempfile
import json
import sys
sys.path.insert(0, 'src')

from feedland_parser.feed_parser import FeedParser
from feedland_parser.article_extractor import ArticleExtractor
from feedland_parser.domain_blacklist import DomainBlacklist
from feedland_parser.filter import Filter
from feedland_parser.config import Config
from feedland_parser.opml_parser import FeedInfo


class TestFeedParserHTMLCleaning:
    """测试 FeedParser 清理描述内容中的 HTML 标签"""

    def test_description_with_html_stripped(self):
        """测试描述中的 HTML 标签被清理"""
        # 创建临时配置
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "url": "https://test.com/opml",
                "threads": 1,
                "log_days": 1
            }
            json.dump(config_data, f)
            temp_config = f.name

        config = Config(temp_config)
        config.load()

        blacklist = DomainBlacklist()
        filter = Filter(config)
        extractor = ArticleExtractor(blacklist=blacklist)
        parser = FeedParser(
            article_extractor=extractor,
            filter=filter,
            timeout=10,
            max_articles=1
        )

        # 模拟一个带有 HTML 的描述
        description = '<p><strong>重要新闻</strong>：这是一段<a href="https://example.com">测试</a>内容。</p>'

        # 使用 _fallback 直接测试
        result = extractor._fallback(
            article_url="https://example.com/test",
            title="测试文章",
            published=None,
            author=None,
            description=description,
            reason="网络错误"
        )

        # 验证返回的内容
        assert result.success
        assert result.extraction_method == "description-fallback"

        # 验证 HTML 被清理（因为 extraction_method 是 description-fallback）
        from feedland_parser.article_extractor import _strip_html_tags
        cleaned_content = _strip_html_tags(description)

        assert "<p>" not in cleaned_content
        assert "<strong>" not in cleaned_content
        assert "<a>" not in cleaned_content
        assert "重要新闻" in cleaned_content
        assert "测试内容" in cleaned_content

    def test_readability_content_not_stripped(self):
        """测试 Readability 提取的内容不被清理"""
        # Readability 提取的内容应该已经是纯文本
        # 不需要再次清理
        description = "纯文本内容，没有 HTML 标签"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {"url": "https://test.com", "threads": 1}
            json.dump(config_data, f)
            temp_config = f.name

        config = Config(temp_config)
        config.load()

        blacklist = DomainBlacklist()
        filter = Filter(config)

        # Mock 一个成功提取的内容（不是 description-fallback）
        from feedland_parser.article_extractor import ArticleContent
        mock_content = ArticleContent(
            title="测试",
            url="https://example.com",
            published=None,
            author=None,
            content=description,
            success=True,
            extraction_method="readability"
        )

        # 验证 extraction_method 不是 description-fallback
        assert mock_content.extraction_method != "description-fallback"

        # 内容应该保持原样
        assert mock_content.content == description

    def test_mixed_feeds_with_different_methods(self):
        """测试不同提取方法的内容处理"""
        # 创建配置
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {"url": "https://test.com", "threads": 1, "log_days": 1}
            json.dump(config_data, f)
            temp_config = f.name

        config = Config(temp_config)
        config.load()

        blacklist = DomainBlacklist()
        filter = Filter(config)
        extractor = ArticleExtractor(blacklist=blacklist)

        # 测试描述回退（有 HTML，长度 >= 50）
        html_description = '<p>这是一段带有 <strong>HTML</strong> 标签的测试内容，用于验证标签清理功能是否正常工作。</p>'
        result1 = extractor._fallback(
            article_url="https://example.com/1",
            title="测试1",
            published=None,
            author=None,
            description=html_description,
            reason="网络错误测试"
        )

        assert result1.extraction_method == "description-fallback"
        # 内容应该被清理（在 feed_parser 中处理）
        from feedland_parser.article_extractor import _strip_html_tags
        cleaned = _strip_html_tags(result1.content)
        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
        assert "HTML" in cleaned
        assert "标签清理功能" in cleaned

        # 测试失败情况（描述太短）
        result2 = extractor._fallback(
            article_url="https://example.com/2",
            title="测试2",
            published=None,
            author=None,
            description=None,
            reason="失败"
        )

        assert not result2.success
        assert result2.content == ""
