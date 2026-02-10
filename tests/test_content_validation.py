"""内容验证测试"""

import pytest
from feedland_parser.article_extractor import ArticleExtractor
from feedland_parser.domain_blacklist import DomainBlacklist
from unittest.mock import patch


class TestContentValidation:
    """内容验证测试"""

    def test_normal_content_is_valid(self):
        """测试正常内容被认为是有效的"""
        extractor = ArticleExtractor()
        
        normal_content = "这是一段正常的中文内容，没有乱码问题。This is normal English content."
        assert extractor._is_content_valid(normal_content) is True

    def test_short_content_is_invalid(self):
        """测试太短的内容被认为是无效的"""
        extractor = ArticleExtractor()
        
        short_content = "太短了"
        assert extractor._is_content_valid(short_content) is False

    def test_null_content_is_invalid(self):
        """测试包含 null 字符的内容被认为是无效的"""
        extractor = ArticleExtractor()
        
        null_content = "Some text" + "\x00\x00\x00\x00\x00" + " more text"
        assert extractor._is_content_valid(null_content) is False

    def test_garbled_content_with_many_control_chars(self):
        """测试包含大量控制字符的内容被认为是无效的"""
        extractor = ArticleExtractor()
        
        # 包含 50 个控制字符的内容
        garbled_content = "A" * 100 + "\x01\x02\x03\x04\x05" * 10 + "B" * 100
        # 总共 200 字符，其中 50 个控制字符，占比 25%，超过 10%
        assert extractor._is_content_valid(garbled_content) is False

    def test_content_with_few_control_chars_is_valid(self):
        """测试包含少量控制字符的内容被认为是有效的"""
        extractor = ArticleExtractor()
        
        # 包含 5 个控制字符的内容
        content_with_few_controls = "A" * 100 + "\x01\x02\x03\x04\x05" + "B" * 100
        # 总共 205 字符，其中 5 个控制字符，占比约 2.4%，低于 10%
        assert extractor._is_content_valid(content_with_few_controls) is True

    def test_content_extraction_with_garbled_data(self):
        """测试提取包含乱码的内容会被拒绝"""
        extractor = ArticleExtractor()
        blacklist = DomainBlacklist()
        extractor.blacklist = blacklist
        
        # 模拟返回包含乱码的内容
        garbled_content = "Some text" + "\x00\x01\x02\x03\x04\x05" * 10 + " more text"
        
        with patch.object(extractor, 'extract_with_cloudscraper', return_value=garbled_content):
            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                description=None
            )
            
            # 应该失败（因为内容有乱码）
            assert result.success is False
            
            # 域名应该在黑名单中
            assert len(blacklist) == 1

    def test_content_extraction_with_valid_data(self):
        """测试提取有效内容会成功"""
        extractor = ArticleExtractor()
        blacklist = DomainBlacklist()
        extractor.blacklist = blacklist
        
        # 模拟返回有效内容
        valid_content = "这是一段正常的中文内容，长度超过100个字符，应该被认为是有效的。This is a longer piece of text that meets the minimum length requirement and does not contain any garbled characters or control characters that would make it invalid."
        
        with patch.object(extractor, 'extract_with_cloudscraper', return_value=valid_content):
            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                description=None
            )
            
            # 应该成功
            assert result.success is True
            assert result.content == valid_content
            
            # 域名不应该在黑名单中
            assert len(blacklist) == 0