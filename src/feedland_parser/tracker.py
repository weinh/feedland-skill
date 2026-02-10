"""时间戳跟踪模块"""

import logging
from typing import Dict, Optional
from datetime import datetime
from .config import Config

logger = logging.getLogger(__name__)


class FeedTracker:
    """Feed 时间戳跟踪器"""

    def __init__(self, config: Config):
        """
        初始化 Feed 跟踪器

        Args:
            config: 配置对象
        """
        self.config = config
        self._history: Dict[str, str] = {}

    def load_history(self) -> Dict[str, str]:
        """
        从配置文件加载历史记录

        Returns:
            历史记录字典 {feed_url: timestamp}
        """
        try:
            self._history = self.config.his.copy()
            logger.info(f"加载历史记录，共 {len(self._history)} 个 feeds")
            return self._history
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self._history = {}
            return {}

    def save_history(self) -> None:
        """
        保存历史记录到配置文件（使用文件锁）

        Raises:
            IOError: 文件写入失败
        """
        try:
            self.config.his = self._history
            self.config.save()
            logger.info(f"保存历史记录，共 {len(self._history)} 个 feeds")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            raise

    def get_last_timestamp(self, feed_url: str) -> Optional[str]:
        """
        获取指定 feed 的最后提取时间

        Args:
            feed_url: feed URL

        Returns:
            最后提取时间戳，如果没有记录则返回 None
        """
        return self._history.get(feed_url)

    def update_timestamp(self, feed_url: str, timestamp: str) -> None:
        """
        更新指定 feed 的最后提取时间

        Args:
            feed_url: feed URL
            timestamp: 时间戳
        """
        self._history[feed_url] = timestamp
        logger.debug(f"更新 feed 时间戳: {feed_url} -> {timestamp}")

    def is_newer_than_last(self, feed_url: str, article_timestamp: str) -> bool:
        """
        检查文章时间戳是否比记录的时间戳更新

        Args:
            feed_url: feed URL
            article_timestamp: 文章时间戳

        Returns:
            如果文章时间戳更新则返回 True，否则返回 False
        """
        last_timestamp = self.get_last_timestamp(feed_url)

        # 如果没有历史记录，认为是新文章
        if not last_timestamp:
            return True

        try:
            # 解析时间戳并比较
            last_dt = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            article_dt = datetime.fromisoformat(article_timestamp.replace("Z", "+00:00"))

            return article_dt > last_dt

        except Exception as e:
            logger.warning(f"比较时间戳失败: {e}")
            # 如果解析失败，保守起见认为是新文章
            return True

    def get_feed_count(self) -> int:
        """
        获取跟踪的 feed 数量

        Returns:
            feed 数量
        """
        return len(self._history)

    def remove_feed(self, feed_url: str) -> None:
        """
        移除指定 feed 的记录

        Args:
            feed_url: feed URL
        """
        if feed_url in self._history:
            del self._history[feed_url]
            logger.debug(f"移除 feed 记录: {feed_url}")

    def clear_history(self) -> None:
        """清空所有历史记录"""
        self._history.clear()
        logger.info("清空所有历史记录")