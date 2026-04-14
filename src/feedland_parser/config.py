"""配置管理模块"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "log_days": 3,
    "log_dir": "~/.feedland/logs",
    "result_file": "~/.feedland/results.json",
}


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.getcwd(), "config.json")
        self._config: Dict[str, Any] = {}
        
        # 确保目录存在
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.isfile(self.config_path):
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
        """保存配置文件"""
        if not self.config_path:
            raise ValueError("未设置配置文件路径")

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"成功保存配置文件: {self.config_path}")
        except IOError as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    # ===== 简化的属性访问 =====
    
    @property
    def url(self) -> Optional[str]:
        return self._config.get("url")

    @url.setter
    def url(self, value: str):
        self._config["url"] = value

    @property
    def threads(self) -> int:
        import multiprocessing
        threads = self._config.get("threads")
        if threads is None:
            return min(10, multiprocessing.cpu_count() * 2 + 1)
        try:
            return int(threads)
        except (ValueError, TypeError):
            return min(10, multiprocessing.cpu_count() * 2 + 1)

    @threads.setter
    def threads(self, value: int):
        self._config["threads"] = value

    @property
    def log_days(self) -> int:
        return self._config.get("log_days", DEFAULT_CONFIG["log_days"])

    @log_days.setter
    def log_days(self, value: int):
        self._config["log_days"] = value

    @property
    def result_file(self) -> str:
        return self._config.get("result_file", DEFAULT_CONFIG["result_file"])

    @result_file.setter
    def result_file(self, value: str):
        self._config["result_file"] = value

    @property
    def log_dir(self) -> str:
        return self._config.get("log_dir", DEFAULT_CONFIG["log_dir"])

    @log_dir.setter
    def log_dir(self, value: str):
        self._config["log_dir"] = value

    @property
    def his(self) -> Dict[str, str]:
        return self._config.get("his", {})

    @his.setter
    def his(self, value: Dict[str, str]):
        self._config["his"] = value

    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.url:
            logger.error("配置缺少必要的 'url' 字段")
            return False
        return True

    def __repr__(self) -> str:
        return f"Config(path={self.config_path}, url={self.url})"
