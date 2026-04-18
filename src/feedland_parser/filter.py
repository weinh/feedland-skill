"""文章过滤模块 - 合并了 FeedTracker 和 Deduplicator"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime
from .config import Config

logger = logging.getLogger(__name__)


class Filter:
    """文章过滤器 - 同时负责时间戳跟踪和去重"""

    def __init__(self, config: Config):
        """
        初始化过滤器

        Args:
            config: 配置对象
        """
        self.config = config
        self._history: Dict[str, str] = {}  # feed_url -> timestamp
        self._lock = threading.Lock()

    # ===== FeedTracker 功能 =====

    def load_history(self) -> Dict[str, str]:
        """从配置文件加载历史记录"""
        try:
            self._history = self.config.his.copy()
            logger.info(f"加载历史记录，共 {len(self._history)} 个 feeds")
            return self._history
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self._history = {}
            return {}

    def save_history(self) -> None:
        """保存历史记录到配置文件"""
        try:
            self.config.his = self._history
            self.config.save()
            logger.info(f"保存历史记录，共 {len(self._history)} 个 feeds")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            raise

    def get_last_timestamp(self, feed_url: str) -> Optional[str]:
        """获取指定 feed 的最后提取时间（兼容旧代码）"""
        return self._history.get(feed_url)

    def get_last_id(self, feed_url: str) -> Optional[str]:
        """获取指定 feed 的最后处理 ID"""
        return self._history.get(feed_url)

    def update_timestamp(self, feed_url: str, timestamp: str) -> None:
        """更新指定 feed 的最后提取时间（兼容旧代码）"""
        with self._lock:
            self._history[feed_url] = timestamp
            logger.debug(f"更新 feed 时间戳: {feed_url} -> {timestamp}")

    def update_id(self, feed_url: str, article_id: str) -> None:
        """更新指定 feed 的最后处理 ID"""
        with self._lock:
            self._history[feed_url] = article_id
            logger.debug(f"更新 feed ID: {feed_url} -> {article_id[:80]}...")

    def is_newer_than_last(self, feed_url: str, article_timestamp: str) -> bool:
        """检查文章时间戳是否比记录的时间戳更新（兼容旧代码）"""
        last_timestamp = self.get_last_timestamp(feed_url)
        if not last_timestamp:
            return True

        try:
            last_dt = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            article_dt = datetime.fromisoformat(article_timestamp.replace("Z", "+00:00"))
            return article_dt > last_dt
        except Exception as e:
            logger.warning(f"比较时间戳失败: {e}")
            return True

    def is_newer_than_last_id(self, feed_url: str, article_id: str) -> bool:
        """检查文章 ID 是否比记录的 ID 更新（支持时间戳比较）"""
        last_id = self.get_last_id(feed_url)
        if not last_id:
            return True

        # 尝试作为时间戳比较
        try:
            last_dt = datetime.fromisoformat(last_id.replace("Z", "+00:00"))
            article_dt = datetime.fromisoformat(article_id.replace("Z", "+00:00"))
            return article_dt > last_dt
        except Exception:
            # 不是时间戳，直接比较字符串
            return article_id != last_id

    def get_feed_count(self) -> int:
        """获取跟踪的 feed 数量"""
        return len(self._history)

    def remove_feed(self, feed_url: str) -> None:
        """移除指定 feed 的记录"""
        with self._lock:
            if feed_url in self._history:
                del self._history[feed_url]
                logger.debug(f"移除 feed 记录: {feed_url}")

    def clear_history(self) -> None:
        """清空所有历史记录"""
        with self._lock:
            self._history.clear()
            logger.info("清空所有历史记录")

    # ===== Deduplicator 功能 =====

    def is_new_article(self, feed_url: str, article_url: str, article_timestamp: str) -> bool:
        """检查文章是否是新文章（未被处理过）"""
        try:
            if not self.is_newer_than_last(feed_url, article_timestamp):
                logger.debug(f"文章时间戳不更新，跳过: {article_url}")
                return False
            return True
        except Exception as e:
            logger.warning(f"检查文章是否新文章时发生错误: {e}")
            return True

    def filter_articles(self, feed_url: str, articles: List[dict]) -> List[dict]:
        """根据时间戳过滤文章，只保留新文章"""
        filtered = []
        for article in articles:
            try:
                article_timestamp = article.get("published")
                if not article_timestamp:
                    logger.warning(f"文章缺少时间戳，默认处理: {article.get('url')}")
                    filtered.append(article)
                    continue

                if self.is_new_article(feed_url, article.get("url", ""), article_timestamp):
                    filtered.append(article)
                else:
                    logger.debug(f"跳过旧文章: {article.get('url')}")
            except Exception as e:
                logger.warning(f"过滤文章时发生错误: {e}")
                filtered.append(article)

        logger.info(f"过滤后保留 {len(filtered)}/{len(articles)} 篇文章")
        return filtered

    def should_skip_article(self, feed_url: str, article_url: str, article_timestamp: str) -> bool:
        """判断是否应该跳过文章"""
        return not self.is_new_article(feed_url, article_url, article_timestamp)
