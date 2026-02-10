"""配置管理模块"""

import json
import os
import fcntl
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """配置管理类，用于读取和保存配置文件"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为 None 则自动查找
        """
        self.config_path = self._find_config_file(config_path)
        self._config: Dict[str, Any] = {}
        self._lock_file = None

        # 确保配置目录存在
        if self.config_path:
            config_dir = os.path.dirname(self.config_path)
            if config_dir:  # 只有当目录非空时才创建
                os.makedirs(config_dir, exist_ok=True)

    def _find_config_file(self, provided_path: Optional[str] = None) -> Optional[str]:
        """
        查找配置文件

        查找优先级：
        1. 命令行参数提供的路径
        2. 当前目录的 config.json
        3. 用户配置目录的 config.json

        Args:
            provided_path: 命令行参数提供的配置文件路径

        Returns:
            找到的配置文件路径，如果没有找到则返回 None
        """
        # 1. 使用命令行参数提供的路径
        if provided_path and os.path.isfile(provided_path):
            return provided_path

        # 2. 查找当前目录
        current_dir_config = os.path.join(os.getcwd(), "config.json")
        if os.path.isfile(current_dir_config):
            return current_dir_config

        # 3. 查找用户配置目录
        user_config_dir = os.path.expanduser("~/.config/yonglelaoren-feedland-parser")
        user_config_path = os.path.join(user_config_dir, "config.json")
        if os.path.isfile(user_config_path):
            return user_config_path

        # 如果都没有找到，返回当前目录的 config.json（可能不存在，用于创建新配置）
        return current_dir_config

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if not self.config_path or not os.path.isfile(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}")
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"成功加载配置文件: {self.config_path}")
            return self._config
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def save(self) -> None:
        """
        保存配置文件（使用文件锁）

        Raises:
            IOError: 文件写入失败
        """
        if not self.config_path:
            raise ValueError("未设置配置文件路径")

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                # 获取文件锁
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                    logger.info(f"成功保存配置文件: {self.config_path}")
                finally:
                    # 释放文件锁
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except IOError as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    @property
    def url(self) -> Optional[str]:
        """获取 OPML URL"""
        return self._config.get("url")

    @url.setter
    def url(self, value: str) -> None:
        """设置 OPML URL"""
        self._config["url"] = value

    @property
    def threads(self) -> int:
        """
        获取线程数

        Returns:
            线程数，如果未配置则返回默认值
        """
        import multiprocessing
        threads = self._config.get("threads")
        if threads is None:
            # 默认值：min(10, cpu_count() * 2 + 1)
            return min(10, multiprocessing.cpu_count() * 2 + 1)
        try:
            return int(threads)
        except (ValueError, TypeError):
            logger.warning(f"线程数配置无效: {threads}，使用默认值")
            return min(10, multiprocessing.cpu_count() * 2 + 1)

    @threads.setter
    def threads(self, value: int) -> None:
        """设置线程数"""
        self._config["threads"] = value

    @property
    def his(self) -> Dict[str, str]:
        """
        获取历史记录

        Returns:
            历史记录字典 {feed_url: timestamp}
        """
        return self._config.get("his", {})

    @his.setter
    def his(self, value: Dict[str, str]) -> None:
        """设置历史记录"""
        self._config["his"] = value

    def update_history(self, feed_url: str, timestamp: str) -> None:
        """
        更新指定 feed 的历史记录

        Args:
            feed_url: feed URL
            timestamp: 时间戳
        """
        if "his" not in self._config:
            self._config["his"] = {}
        self._config["his"][feed_url] = timestamp

    def validate(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        if not self.url:
            logger.error("配置缺少必要的 'url' 字段")
            return False
        return True

    def __repr__(self) -> str:
        return f"Config(path={self.config_path}, url={self.url})"