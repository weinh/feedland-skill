"""Feed 解析模块"""

import logging
import feedparser
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from .article_extractor import ArticleExtractor, ArticleContent
from .deduplicator import Deduplicator
from .opml_parser import FeedInfo

logger = logging.getLogger(__name__)


@dataclass
class FeedResult:
    """Feed 解析结果"""

    feed_info: FeedInfo
    articles: List[Dict]
    success: bool
    error: Optional[str] = None


class FeedParser:
    """Feed 解析器"""

    def __init__(
        self,
        article_extractor: ArticleExtractor,
        deduplicator: Deduplicator,
        timeout: int = 10,
        max_articles: int = 5,
        max_retries: int = 3
    ):
        """
        初始化 Feed 解析器

        Args:
            article_extractor: 文章提取器
            deduplicator: 去重器
            timeout: 请求超时时间（秒）
            max_articles: 每个 feed 最多提取的文章数
            max_retries: 最大重试次数
        """
        self.article_extractor = article_extractor
        self.deduplicator = deduplicator
        self.timeout = timeout
        self.max_articles = max_articles
        self.max_retries = max_retries

    def parse_feed(self, feed_info: FeedInfo) -> FeedResult:
        """
        解析单个 feed

        Args:
            feed_info: Feed 信息

        Returns:
            Feed 解析结果
        """
        try:
            # 使用重试机制获取 feed
            feed_data = self._fetch_feed_with_retry(feed_info.url)

            if not feed_data:
                return FeedResult(
                    feed_info=feed_info,
                    articles=[],
                    success=False,
                    error="无法获取 feed 数据"
                )

            # 解析文章
            articles = self._parse_articles(feed_info, feed_data)

            return FeedResult(
                feed_info=feed_info,
                articles=articles,
                success=True
            )

        except Exception as e:
            logger.error(f"解析 feed 失败 {feed_info.url}: {e}")
            return FeedResult(
                feed_info=feed_info,
                articles=[],
                success=False,
                error=str(e)
            )

    def _fetch_feed_with_retry(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """
        带重试机制的 feed 获取

        Args:
            feed_url: feed URL

        Returns:
            feed 数据，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                # 使用 User-Agent 避免被某些网站拒绝
                user_agent = "Mozilla/5.0 (compatible; yonglelaoren-feedland-parser/1.0.0)"
                feed = feedparser.parse(feed_url, agent=user_agent)

                if feed.bozo:
                    logger.warning(f"Feed 解析警告 {feed_url}: {feed.bozo_exception}")

                return feed

            except Exception as e:
                logger.warning(f"获取 feed 失败 (尝试 {attempt + 1}/{self.max_retries}) {feed_url}: {e}")
                if attempt < self.max_retries - 1:
                    continue
                else:
                    return None

        return None

    def _parse_articles(
        self,
        feed_info: FeedInfo,
        feed_data: feedparser.FeedParserDict
    ) -> List[Dict]:
        """
        解析文章

        Args:
            feed_info: Feed 信息
            feed_data: feed 数据

        Returns:
            文章列表
        """
        articles = []
        total_processed = 0  # 已处理的条目总数

        # 获取该 feed 的最后获取时间
        last_timestamp = None
        if hasattr(self.deduplicator, 'tracker') and self.deduplicator.tracker:
            last_timestamp = self.deduplicator.tracker.get_last_timestamp(feed_info.url)

        for entry in feed_data.entries:
            # 检查是否已经处理了足够的文章
            if len(articles) >= self.max_articles:
                logger.debug(f"已达到最大文章数限制 ({self.max_articles})，停止处理")
                break
            
            total_processed += 1
            
            try:
                # 获取文章 URL
                article_url = entry.get("link")
                if not article_url:
                    logger.debug(f"文章缺少 URL，跳过: {entry.get('title', 'Unknown')}")
                    continue

                # 获取发布日期
                published = self._parse_published_date(entry)

                # 检查是否达到历史获取时间（不处理更旧的文章）
                if last_timestamp and published:
                    try:
                        from datetime import datetime
                        last_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                        published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        
                        if published_dt <= last_dt:
                            logger.debug(f"文章发布时间 {published} 不晚于历史时间 {last_timestamp}，停止处理")
                            break
                    except Exception as e:
                        logger.debug(f"比较日期时间失败: {e}")

                # 获取文章标题
                title = entry.get("title", "Unknown")

                # 获取作者
                author = entry.get("author") or entry.get("author_detail", {}).get("name")

                # 获取描述内容
                description = self._get_description(entry)

                # 提取文章内容
                article_content = self.article_extractor.extract(
                    article_url,
                    title=title,
                    published=published,
                    author=author,
                    description=description
                )

                if not article_content.success or not article_content.content:
                    logger.warning(f"文章内容提取失败: {article_url}")
                    continue

                # 创建文章字典
                article = {
                    "title": article_content.title,
                    "url": article_content.url,
                    "published": article_content.published,
                    "author": article_content.author,
                    "content": article_content.content,
                }

                articles.append(article)

            except Exception as e:
                logger.warning(f"解析文章时发生错误: {e}")
                continue

        # 按时间排序（只对已获取的文章排序）
        articles.sort(key=lambda x: x["published"] or "", reverse=True)

        logger.info(f"从 {feed_info.url} 解析了 {len(articles)} 篇文章（共检查了 {total_processed} 个条目）")
        return articles

    def _get_description(self, entry: feedparser.FeedParserDict) -> Optional[str]:
        """
        从条目中获取描述内容

        Args:
            entry: feed 条目

        Returns:
            描述内容，如果没有则返回 None
        """
        # 尝试多种描述字段
        for field in ["description", "summary", "content"]:
            value = entry.get(field)
            if value:
                # 如果是字典（例如 content 字段），获取 value
                if isinstance(value, dict):
                    value = value.get("value")
                # 如果是列表，获取第一个
                elif isinstance(value, list) and len(value) > 0:
                    value = value[0]
                    if isinstance(value, dict):
                        value = value.get("value")
                
                if value and isinstance(value, str):
                    return value
        
        return None

    def _parse_published_date(self, entry: feedparser.FeedParserDict) -> Optional[str]:
        """
        解析发布日期

        Args:
            entry: feed 条目

        Returns:
            ISO 8601 格式的日期字符串
        """
        # 尝试多种日期字段
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]

        for field in date_fields:
            date_struct = entry.get(field)
            if date_struct:
                try:
                    dt = datetime(*date_struct[:6])
                    return dt.isoformat()
                except Exception:
                    continue

        return None

    def parse_feeds(self, feed_infos: List[FeedInfo]) -> List[FeedResult]:
        """
        批量解析 feeds

        Args:
            feed_infos: Feed 信息列表

        Returns:
            Feed 结果列表
        """
        results = []

        for feed_info in feed_infos:
            result = self.parse_feed(feed_info)
            results.append(result)

        # 统计
        success_count = sum(1 for r in results if r.success)
        logger.info(f"解析完成: {success_count}/{len(results)} 个 feeds 成功")

        return results