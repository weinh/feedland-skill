"""文章提取器测试 - 包含真实 URL 的提取测试"""

import pytest
from feedland_parser import ArticleExtractor


class TestArticleExtractorWithRealURL:
    """文章提取器测试 - 使用真实 URL"""

    @pytest.fixture
    def extractor(self):
        """创建文章提取器"""
        return ArticleExtractor(timeout=15)

    def test_extract_openai_article(self, extractor):
        """测试提取 OpenAI 文章内容"""
        url = "https://openai.com/index/pvh-future-of-fashion"
        
        result = extractor.extract(
            url,
            title="PVH Future of Fashion",
            published="2025-02-09T10:00:00Z",
            author="OpenAI"
        )
        
        # 验证结果
        assert result.url == url
        assert result.title == "PVH Future of Fashion"
        assert result.author == "OpenAI"
        
        # 验证内容
        if result.success:
            assert len(result.content) > 0, "成功提取时内容不应为空"
            print(f"\n✅ 提取成功!")
            print(f"   内容长度: {len(result.content)} 字符")
            print(f"   前 100 字符: {result.content[:100]}...")
        else:
            pytest.fail(f"文章提取失败: {url}")

    def test_extract_with_missing_content(self, extractor):
        """测试提取内容不足的情况"""
        # 使用一个可能没有内容或内容很少的 URL
        url = "https://example.com/short-page"
        
        result = extractor.extract(
            url,
            title="Short Page",
            published="2025-02-09T10:00:00Z",
            author="Test Author"
        )
        
        # 验证结果
        assert result.url == url
        # 这个测试可能会成功也可能失败，取决于实际内容
        print(f"\n提取结果: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"   内容长度: {len(result.content)} 字符")

    def test_extract_with_invalid_url(self, extractor):
        """测试无效 URL"""
        url = "https://this-domain-does-not-exist-12345.com/article"
        
        result = extractor.extract(
            url,
            title="Invalid URL Test",
            published="2025-02-09T10:00:00:00Z",
            author="Test Author"
        )
        
        # 无效 URL 应该失败
        assert result.url == url
        assert not result.success
        assert result.content == ""
        print(f"\n✅ 无效 URL 正确处理为失败状态")

    def test_extract_with_timeout(self, extractor):
        """测试超时情况"""
        # 创建一个会超时的测试
        slow_extractor = ArticleExtractor(timeout=1)
        
        # 使用一个可能响应慢的 URL
        url = "https://httpbin.org/delay/5"
        
        result = slow_extractor.extract(
            url,
            title="Timeout Test",
            published="2025-02-09T10:00:00Z",
            author="Test"
        )
        
        assert result.url == url
        # 超时应该失败
        assert not result.success
        print(f"\n✅ 超时情况正确处理")

    def test_extract_with_multiple_articles(self, extractor):
        """测试提取多个文章"""
        urls = [
            "https://openai.com/index/pvh-future-of-fashion",
            "https://openai.com/index/our-approach-to-localization",
        ]
        
        results = []
        for url in urls:
            result = extractor.extract(
                url,
                title=f"Article from {url}",
                published="2025-02-09T10:00:00Z",
                author="OpenAI"
            )
            results.append(result)
            print(f"\nURL: {url}")
            print(f"  成功: {result.success}")
            print(f"  内容长度: {len(result.content) if result.success else 0}")
        
        # 验证至少有一个成功
        successful = [r for r in results if r.success]
        assert len(successful) >= 1, "至少应该有一个文章提取成功"
        
        print(f"\n✅ 多文章测试完成: {len(successful)}/{len(urls)} 成功")

    def test_extract_content_quality(self, extractor):
        """测试提取内容的质量"""
        url = "https://openai.com/index/pvh-future-of-fashion"
        
        result = extractor.extract(
            url,
            title="Content Quality Test",
            published="2025-02-09T10:00:00Z",
            author="OpenAI"
        )
        
        if result.success:
            # 验证内容质量
            content = result.content
            
            # 内容应该足够长
            assert len(content) > 500, f"内容应该至少 500 字符，实际: {len(content)}"
            
            # 内容应该包含常见的文章标记（标题、段落等）
            # 这里只是简单的长度检查，更复杂的检查需要 NLP
            
            # 内容不应该只包含空白字符
            assert len(content.strip()) > 0, "内容不应只包含空白"
            
            # 内容应该包含一些字母数字
            alnum_count = sum(c.isalnum() for c in content)
            assert alnum_count > 100, f"内容应该包含足够的字母数字，实际: {alnum_count}"
            
            print(f"\n✅ 内容质量验证通过:")
            print(f"   总长度: {len(content)}")
            print(f"   非空长度: {len(content.strip())}")
            print(f"   字母数字数: {alnum_count}")
        else:
            pytest.fail("提取失败，无法验证内容质量")

    def test_extract_with_different_feeds(self, extractor):
        """测试从不同 feed 源提取文章"""
        test_cases = [
            ("https://openai.com/blog/rss.xml", "https://openai.com/blog/"),
            ("https://blog.feedspot.com/feeds/posts/default", "https://example-blog.blogspot.com/"),
        ]
        
        for feed_url, article_url in test_cases:
            print(f"\n测试 feed: {feed_url}")
            print(f"  文章: {article_url}")
            
            # 这里我们只测试能否访问 feed，不实际提取所有文章
            import feedparser
            try:
                feed = feedparser.parse(feed_url)
                if feed.entries:
                    # 尝试提取第一篇文章
                    first_entry = feed.entries[0]
                    article_url_to_extract = first_entry.get('link')
                    if article_url_to_extract:
                        result = extractor.extract(
                            article_url_to_extract,
                            title=first_entry.get('title'),
                            published=first_entry.get('published'),
                            author="Test"
                        )
                        print(f"  提取结果: {'成功' if result.success else '失败'}")
                        if result.success:
                            print(f"  内容长度: {len(result.content)}")
                        else:
                            print(f"  失败原因: 内容不足或提取错误")
            except Exception as e:
                print(f"  Feed 解析失败: {e}")


class TestArticleExtractorErrorScenarios:
    """文章提取器错误场景测试"""

    @pytest.fixture
    def extractor(self):
        """创建文章提取器"""
        return ArticleExtractor(timeout=10)

    def test_extract_with_404_error(self, extractor):
        """测试 404 错误"""
        url = "https://openai.com/nonexistent-page-404"
        
        result = extractor.extract(
            url,
            title="404 Test",
            published="2025-02-09T10:00:00Z",
            author="Test"
        )
        
        assert result.url == url
        assert not result.success
        print(f"\n✅ 404 错误正确处理")

    def test_extract_with_redirect_loop(self, extractor):
        """测试重定向循环"""
        # 使用一个可能有重定向问题的 URL
        url = "https://httpbin.org/redirect/10"
        
        result = extractor.extract(
            url,
            title="Redirect Test",
            published="2025-02-09T10:00:00Z",
            author="Test"
        )
        
        assert result.url == url
        # 重定向循环可能成功也可能失败
        print(f"\n重定向测试: {'成功' if result.success else '失败'}")

    def test_extract_with_large_page(self, extractor):
        """测试大页面提取"""
        url = "https://openai.com/index"  # OpenAI 首页可能有大量内容
        
        result = extractor.extract(
            url,
            title="Large Page Test",
            published="2025-02-09T10:00:00Z",
            author="OpenAI"
        )
        
        assert result.url == url
        if result.success:
            print(f"\n✅ 大页面提取成功: {len(result.content)} 字符")
        else:
            print(f"\n⚠️  大页面提取失败")

    def test_extract_with_encoding_issues(self, extractor):
        """测试编码问题"""
        # 使用可能有特殊字符的页面
        url = "https://openai.com/index/pvh-future-of-fashion"
        
        result = extractor.extract(
            url,
            title="Encoding Test",
            published="2025-02-09T10:00:00Z",
            author="Test"
        )
        
        if result.success:
            # 验证内容可以被序列化为 JSON
            import json
            try:
                json.dumps({"content": result.content})
                print(f"\n✅ 编码测试通过: JSON 序列化成功")
            except (UnicodeEncodeError, TypeError) as e:
                pytest.fail(f"内容包含无法编码的字符: {e}")
        else:
            print(f"\n⚠️  提取失败，无法测试编码")