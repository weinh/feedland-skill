"""Feed 解析模块单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from feedland_parser.feed_parser import FeedParser, FeedResult
from feedland_parser.opml_parser import FeedInfo
from feedland_parser.article_extractor import ArticleExtractor, ArticleContent
from feedland_parser.deduplicator import Deduplicator


class TestFeedParser:
    """FeedParser 类测试"""

    @pytest.fixture
    def article_extractor(self):
        """创建 ArticleExtractor 实例"""
        return MagicMock(spec=ArticleExtractor)

    @pytest.fixture
    def deduplicator(self):
        """创建 Deduplicator 实例"""
        return MagicMock(spec=Deduplicator)

    @pytest.fixture
    def feed_parser(self, article_extractor, deduplicator):
        """创建 FeedParser 实例"""
        return FeedParser(
            article_extractor=article_extractor,
            deduplicator=deduplicator,
            timeout=10,
            max_articles=5,
            max_retries=3
        )

    def test_parse_feed_success(self, feed_parser, article_extractor):
        """测试成功解析 feed"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        # 模拟文章提取
        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="Test content",
            success=True
        )

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                {
                    "link": "https://example.com/article",
                    "title": "Test Article",
                    "published_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0),
                    "author": "Test Author",
                }
            ]
            mock_parse.return_value = mock_feed

            result = feed_parser.parse_feed(feed_info)

            assert result.success is True
            assert len(result.articles) == 1

    def test_parse_feed_network_error(self, feed_parser):
        """测试网络错误"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        with patch("feedparser.parse") as mock_parse:
            mock_parse.side_effect = Exception("Network error")

            result = feed_parser.parse_feed(feed_info)

            assert result.success is False
            assert result.error is not None

    def test_parse_feed_max_articles(self, feed_parser, article_extractor):
        """测试限制文章数量"""
        feed_parser.max_articles = 3

        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        # 模拟文章提取
        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="Test content",
            success=True
        )

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                {
                    "link": f"https://example.com/article{i}",
                    "title": f"Article {i}",
                    "published_parsed": (2025, 2, 9, 10 + i, 0, 0, 0, 0, 0),
                }
                for i in range(10)
            ]
            mock_parse.return_value = mock_feed

            result = feed_parser.parse_feed(feed_info)

            assert result.success is True
            assert len(result.articles) == 3

    def test_parse_feed_retry_mechanism(self, feed_parser, article_extractor):
        """测试重试机制"""
        feed_parser.max_retries = 3

        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="Test content",
            success=True
        )

        with patch("feedparser.parse") as mock_parse:
            # 前两次失败，第三次成功
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                {
                    "link": "https://example.com/article",
                    "title": "Test Article",
                    "published_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0),
                }
            ]

            mock_parse.side_effect = [Exception("Network error"), Exception("Network error"), mock_feed]

            result = feed_parser.parse_feed(feed_info)

            assert result.success is True
            assert mock_parse.call_count == 3

    def test_parse_feed_extract_failure(self, feed_parser, article_extractor):
        """测试文章提取失败"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        # 模拟文章提取失败
        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="",
            success=False
        )

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                {
                    "link": "https://example.com/article",
                    "title": "Test Article",
                    "published_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0),
                }
            ]
            mock_parse.return_value = mock_feed

            result = feed_parser.parse_feed(feed_info)

            assert result.success is True
            assert len(result.articles) == 0

    def test_parse_feeds_multiple(self, feed_parser, article_extractor):
        """测试批量解析多个 feeds"""
        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="Test content",
            success=True
        )

        feed_infos = [
            FeedInfo(url=f"https://example.com/feed{i}.xml", title=f"Feed {i}", feed_type="RSS")
            for i in range(3)
        ]

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                {
                    "link": "https://example.com/article",
                    "title": "Test Article",
                    "published_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0),
                }
            ]
            mock_parse.return_value = mock_feed

            results = feed_parser.parse_feeds(feed_infos)

            assert len(results) == 3
            assert all(r.success for r in results)

    def test_parse_published_date_various_formats(self, feed_parser):
        """测试解析各种日期格式"""
        # 测试 published_parsed
        entry = {"published_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0)}
        date = feed_parser._parse_published_date(entry)
        assert date is not None

        # 测试 updated_parsed
        entry = {"updated_parsed": (2025, 2, 9, 10, 0, 0, 0, 0, 0)}
        date = feed_parser._parse_published_date(entry)
        assert date is not None

        # 测试没有日期
        entry = {}
        date = feed_parser._parse_published_date(entry)
        assert date is None

    def test_timeout_setting(self):
        """测试超时设置"""
        extractor = MagicMock(spec=ArticleExtractor)
        deduplicator = MagicMock(spec=Deduplicator)

        parser = FeedParser(extractor, deduplicator, timeout=20)
        assert parser.timeout == 20

    def test_max_articles_setting(self):
        """测试最大文章数设置"""
        extractor = MagicMock(spec=ArticleExtractor)
        deduplicator = MagicMock(spec=Deduplicator)

        parser = FeedParser(extractor, deduplicator, max_articles=10)
        assert parser.max_articles == 10

    def test_max_retries_setting(self):
        """测试最大重试次数设置"""
        extractor = MagicMock(spec=ArticleExtractor)
        deduplicator = MagicMock(spec=Deduplicator)

        parser = FeedParser(extractor, deduplicator, max_retries=5)
        assert parser.max_retries == 5

    def test_description_passed_to_extractor(self, feed_parser, article_extractor):
        """测试描述内容被正确传递给提取器"""
        feed_info = FeedInfo(
            url="https://example.com/feed.xml",
            title="Test Feed",
            feed_type="RSS"
        )

        # 模拟文章提取
        article_extractor.extract.return_value = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            published="2025-02-09T10:00:00Z",
            author="Test Author",
            content="Test content",
            success=True
        )

        # 模拟 feed 数据，包含描述内容
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "link": "https://example.com/article",
                "title": "Article 1",
                "description": "This is a description of the article",
            },
        ]

        feed_parser._parse_articles(feed_info, mock_feed)

        # 验证 extract 被调用时传递了 description 参数
        article_extractor.extract.assert_called_once()
        call_kwargs = article_extractor.extract.call_args.kwargs
        assert "description" in call_kwargs
        assert call_kwargs["description"] == "This is a description of the article"