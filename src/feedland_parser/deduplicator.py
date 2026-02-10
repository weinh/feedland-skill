"""去重逻辑模块"""

import logging
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs, urlunparse
from .tracker import FeedTracker

logger = logging.getLogger(__name__)


class Deduplicator:
    """文章去重器"""

    def __init__(self, tracker: FeedTracker):
        """
        初始化去重器

        Args:
            tracker: Feed 跟踪器
        """
        self.tracker = tracker

    def is_new_article(self, feed_url: str, article_url: str, article_timestamp: str) -> bool:
        """
        检查文章是否是新文章（未被处理过）

        Args:
            feed_url: feed URL
            article_url: 文章 URL
            article_timestamp: 文章时间戳

        Returns:
            如果是新文章返回 True，否则返回 False
        """
        try:
            # 检查文章时间戳是否比 feed 的最后提取时间更新
            if not self.tracker.is_newer_than_last(feed_url, article_timestamp):
                logger.debug(f"文章时间戳不更新，跳过: {article_url}")
                return False

            return True

        except Exception as e:
            logger.warning(f"检查文章是否新文章时发生错误: {e}")
            # 容错处理：出错时认为是新文章
            return True

    def normalize_url(self, url: str) -> str:
        """
        标准化 URL（移除跟踪参数）

        Args:
            url: 原始 URL

        Returns:
            标准化后的 URL
        """
        try:
            parsed = urlparse(url)

            # 常见的跟踪参数
            tracking_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "fbclid", "gclid", "msclkid", "_ga", "_gid", "ref", "source", "via"
            }

            # 过滤跟踪参数
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items()
                if k.lower() not in tracking_params
            }

            # 重建 URL
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                # 重新组合查询参数
                "&".join(f"{k}={v[0]}" for k, v in filtered_params.items()),
                parsed.fragment
            ))

            return normalized

        except Exception as e:
            logger.warning(f"标准化 URL 失败: {e}")
            return url

    def filter_articles_by_timestamp(self, feed_url: str, articles: list) -> list:
        """
        根据时间戳过滤文章，只保留新文章

        Args:
            feed_url: feed URL
            articles: 文章列表

        Returns:
            过滤后的文章列表
        """
        filtered = []
        for article in articles:
            try:
                # 获取文章时间戳
                article_timestamp = article.get("published")
                if not article_timestamp:
                    logger.warning(f"文章缺少时间戳，默认处理: {article.get('url')}")
                    filtered.append(article)
                    continue

                # 检查是否是新文章
                if self.is_new_article(feed_url, article.get("url", ""), article_timestamp):
                    filtered.append(article)
                else:
                    logger.debug(f"跳过旧文章: {article.get('url')}")

            except Exception as e:
                logger.warning(f"过滤文章时发生错误: {e}")
                # 容错处理：出错时保留文章
                filtered.append(article)

        logger.info(f"过滤后保留 {len(filtered)}/{len(articles)} 篇文章")
        return filtered

    def should_skip_article(self, feed_url: str, article_url: str, article_timestamp: str) -> bool:
        """
        判断是否应该跳过文章（已处理过）

        Args:
            feed_url: feed URL
            article_url: 文章 URL
            article_timestamp: 文章时间戳

        Returns:
            如果应该跳过返回 True，否则返回 False
        """
        return not self.is_new_article(feed_url, article_url, article_timestamp)