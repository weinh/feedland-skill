"""文章内容提取模块单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from feedland_parser.article_extractor import ArticleExtractor, ArticleContent


class TestArticleExtractor:
    """ArticleExtractor 类测试"""

    @pytest.fixture
    def extractor(self):
        """创建 ArticleExtractor 实例"""
        return ArticleExtractor()

    def test_parse_timestamp_valid(self, extractor):
        """测试解析有效时间戳"""
        # ISO 8601 格式
        assert extractor._parse_timestamp("2025-02-09T10:00:00Z") is not None

        # RFC 2822 格式
        assert extractor._parse_timestamp("Sun, 09 Feb 2025 10:00:00 GMT") is not None

        # 简单日期格式
        assert extractor._parse_timestamp("2025-02-09") is not None

    def test_parse_timestamp_invalid(self, extractor):
        """测试解析无效时间戳"""
        assert extractor._parse_timestamp(None) is None
        assert extractor._parse_timestamp("") is None
        assert extractor._parse_timestamp("invalid") is None

    def test_extract_metadata_success(self, extractor):
        """测试成功提取元数据"""
        with patch("newspaper.Article") as mock_article_class:
            mock_article = MagicMock()
            mock_article.title = "Test Article"
            mock_article.publish_date = None
            mock_article.authors = ["Test Author"]
            mock_article_class.return_value = mock_article

            metadata = extractor.extract_metadata("https://example.com/article")

            assert metadata["title"] == "Test Article"
            assert metadata["url"] == "https://example.com/article"
            assert metadata["author"] == "Test Author"

    def test_extract_metadata_failure(self, extractor):
        """测试提取元数据失败"""
        with patch("newspaper.Article") as mock_article_class:
            mock_article_class.side_effect = Exception("Network error")
            
            metadata = extractor.extract_metadata("https://example.com/article")
            
            assert metadata["title"] == "Unknown"
            assert metadata["url"] == "https://example.com/article"
            assert metadata["author"] is None

    def test_extract_with_description_fallback(self, extractor):
        """测试使用描述内容作为回退"""
        # 模拟所有提取方法都失败
        with patch.object(extractor, 'extract_with_cloudscraper', return_value=None), \
             patch.object(extractor, 'extract_with_newspaper3k', return_value=None), \
             patch.object(extractor, 'extract_with_beautifulsoup', return_value=None):
            
            description = "This is a detailed description of the article content that is at least 50 characters long."
            
            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                description=description
            )
            
            # 应该使用描述内容
            assert result.success is True
            assert result.content == description
            assert result.title == "Test Article"

    def test_extract_with_short_description_no_fallback(self, extractor):
        """测试短描述不作为回退"""
        # 模拟所有提取方法都失败
        with patch.object(extractor, 'extract_with_cloudscraper', return_value=None), \
             patch.object(extractor, 'extract_with_newspaper3k', return_value=None), \
             patch.object(extractor, 'extract_with_beautifulsoup', return_value=None):
            
            # 短描述（少于 50 字符）
            description = "Short description."
            
            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                description=description
            )
            
            # 不应该使用短描述
            assert result.success is False
            assert result.content == ""

    def test_extract_with_description_fallback_on_exception(self, extractor):
        """测试异常时使用描述内容作为回退"""
        # 模拟提取方法抛出异常
        with patch.object(extractor, 'extract_with_cloudscraper', side_effect=Exception("Network error")):
            
            description = "This is a detailed description of the article content that is at least 50 characters long."
            
            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                description=description
            )
            
            # 应该使用描述内容
            assert result.success is True
            assert result.content == description

    def test_blacklisted_domain_uses_description(self, extractor):
        """测试黑名单中的域名直接使用描述内容"""
        from feedland_parser.domain_blacklist import DomainBlacklist
        
        # 创建黑名单并添加域名
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("https://example.com/article", reason="Test")
        extractor.blacklist = blacklist
        
        description = "This is a detailed description of the article content that is at least 50 characters long."
        
        result = extractor.extract(
            "https://example.com/article",
            title="Test Article",
            description=description
        )
        
        # 应该直接使用描述内容，不尝试提取
        assert result.success is True
        assert result.content == description

    def test_blacklisted_domain_no_description_skips(self, extractor):
        """测试黑名单中的域名无描述内容时跳过"""
        from feedland_parser.domain_blacklist import DomainBlacklist
        
        # 创建黑名单并添加域名
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("https://example.com/article", reason="Test")
        extractor.blacklist = blacklist
        
        result = extractor.extract(
            "https://example.com/article",
            title="Test Article",
            description=None
        )
        
        # 应该跳过解析
        assert result.success is False
        assert result.content == ""

    def test_url_failure_with_description_not_blacklisted(self, extractor):
            """测试 URL 失败但有描述内容时，域名会被添加到黑名单"""
            from feedland_parser.domain_blacklist import DomainBlacklist
    
            # 创建黑名单
            blacklist = DomainBlacklist()
            extractor.blacklist = blacklist
    
            # 模拟所有提取方法都失败
            with patch.object(extractor, 'extract_with_cloudscraper', return_value=None), \
                 patch.object(extractor, 'extract_with_newspaper3k', return_value=None), \
                 patch.object(extractor, 'extract_with_beautifulsoup', return_value=None):
                
                description = "This is a detailed description of the article content that is at least 50 characters long."
                
                result = extractor.extract(
                    "https://example.com/article",
                    title="Test Article",
                    description=description
                )
    
                # 应该使用描述内容，成功
                assert result.success is True
                assert result.content == description
                
                # 域名应该在黑名单中（因为 URL 失败）
                assert len(blacklist) == 1
    def test_url_failure_without_description_blacklisted(self, extractor):
            """测试 URL 失败且无描述内容时，域名会被添加到黑名单"""
            from feedland_parser.domain_blacklist import DomainBlacklist
    
            # 创建黑名单
            blacklist = DomainBlacklist()
            extractor.blacklist = blacklist
    
            # 模拟所有提取方法都失败（返回 None 或空字符串）
            with patch.object(extractor, 'extract_with_cloudscraper', return_value=None), \
                 patch.object(extractor, 'extract_with_newspaper3k', return_value=None), \
                 patch.object(extractor, 'extract_with_beautifulsoup', return_value=None):
                
                result = extractor.extract(
                    "https://example.com/article",
                    title="Test Article",
                    description=None
                )
    
                # 应该失败
                assert result.success is False
                assert result.content == ""
    
                # 域名应该在黑名单中
                assert len(blacklist) == 1
    
        def test_content_with_garbled_characters(self, extractor):
            """测试内容包含乱码时被视为失败"""
            from feedland_parser.domain_blacklist import DomainBlacklist
    
            # 创建黑名单
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
                assert len(blacklist) == 1            assert blacklist.is_blacklisted("https://example.com/article")

    def test_extract_with_newspaper3k_success(self, extractor):
        """测试使用 Newspaper3k 成功提取"""
        with patch("newspaper.Article") as mock_article_class:
            mock_article = MagicMock()
            mock_article.text = "This is a long article content that exceeds 100 characters."
            mock_article_class.return_value = mock_article

            content = extractor.extract_with_newspaper3k("https://example.com/article")

            assert content is not None
            assert len(content) > 100

    def test_extract_with_newspaper3k_short_content(self, extractor):
        """测试 Newspaper3k 提取内容太短"""
        with patch("newspaper.Article") as mock_article_class:
            mock_article = MagicMock()
            mock_article.text = "Short"
            mock_article_class.return_value = mock_article

            content = extractor.extract_with_newspaper3k("https://example.com/article")

            assert content is None

    def test_extract_with_newspaper3k_failure(self, extractor):
        """测试 Newspaper3k 提取失败"""
        with patch("newspaper.Article") as mock_article_class:
            mock_article_class.side_effect = Exception("Download failed")

            content = extractor.extract_with_newspaper3k("https://example.com/article")

            assert content is None

    def test_extract_with_beautifulsoup_success(self, extractor):
        """测试使用 BeautifulSoup 成功提取"""
        html = """<!DOCTYPE html>
<html>
<body>
    <article>
        <p>This is a long article content that exceeds 100 characters to ensure it passes the minimum length check.</p>
    </article>
</body>
</html>"""

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = html.encode("utf-8")
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            content = extractor.extract_with_beautifulsoup("https://example.com/article")

            assert content is not None
            assert len(content) > 100

    def test_extract_with_beautifulsoup_failure(self, extractor):
        """测试 BeautifulSoup 提取失败"""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Request failed")

            content = extractor.extract_with_beautifulsoup("https://example.com/article")

            assert content is None

    def test_extract_success(self, extractor):
        """测试成功提取文章"""
        with patch.object(extractor, "extract_with_newspaper3k") as mock_newspaper:
            mock_newspaper.return_value = "This is a long article content that exceeds 100 characters."

            result = extractor.extract(
                "https://example.com/article",
                title="Test Article",
                published="2025-02-09T10:00:00Z",
                author="Test Author"
            )

            assert result.success is True
            assert result.title == "Test Article"
            assert result.url == "https://example.com/article"
            assert result.author == "Test Author"
            assert len(result.content) > 100

    def test_extract_fallback_to_beautifulsoup(self, extractor):
        """测试回退到 BeautifulSoup"""
        with patch.object(extractor, "extract_with_newspaper3k") as mock_newspaper, \
             patch.object(extractor, "extract_with_beautifulsoup") as mock_bs:
            mock_newspaper.return_value = "Short"
            mock_bs.return_value = "This is a long article content that exceeds 100 characters."

            result = extractor.extract("https://example.com/article")

            assert result.success is True
            assert len(result.content) > 100

    def test_extract_complete_failure(self, extractor):
        """测试完全提取失败"""
        with patch.object(extractor, "extract_with_newspaper3k") as mock_newspaper, \
             patch.object(extractor, "extract_with_beautifulsoup") as mock_bs:
            mock_newspaper.return_value = None
            mock_bs.return_value = None

            result = extractor.extract("https://example.com/article")

            assert result.success is False
            assert result.content == ""

    def test_timeout_setting(self):
        """测试超时设置"""
        extractor = ArticleExtractor(timeout=20)
        assert extractor.timeout == 20
