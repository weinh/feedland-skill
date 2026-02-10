"""域名黑名单模块"""

import logging
from typing import Optional, Set, List
from urllib.parse import urlparse
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class DomainBlacklist:
    """域名黑名单管理类（线程安全）"""

    def __init__(self, initial_blacklist: Optional[Set[str]] = None):
        """
        初始化域名黑名单管理器

        Args:
            initial_blacklist: 初始黑名单集合
        """
        self._blacklist: Set[str] = initial_blacklist or set()
        self._blacklist_metadata: dict = {}  # 存储每个黑名单条目的元数据（添加时间、失败次数等）
        self._lock = Lock()  # 线程锁，确保黑名单操作的线程安全

    @staticmethod
    def get_domain_from_url(url: str) -> Optional[str]:
        """
        从 URL 提取域名

        Args:
            url: URL 字符串

        Returns:
            域名，如果 URL 无效则返回 None
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # 如果没有协议或域名，返回 None
            if not domain:
                return None
            # 移除 www. 前缀
            if domain.startswith("www."):
                domain = domain[4:]
            # 再次检查是否为空
            if not domain:
                return None
            return domain
        except Exception as e:
            logger.warning(f"从 URL 提取域名失败: {url}, 错误: {e}")
            return None

    def is_blacklisted(self, url_or_domain: str) -> bool:
        """
        检查域名是否在黑名单中

        Args:
            url_or_domain: URL 或域名

        Returns:
            如果域名在黑名单中返回 True，否则返回 False
        """
        with self._lock:
            # 如果输入是域名，直接检查
            if url_or_domain in self._blacklist:
                return True

            # 如果输入是 URL，提取域名后检查
            domain = self.get_domain_from_url(url_or_domain)
            if domain and domain in self._blacklist:
                return True

            return False

    def add_to_blacklist(self, url_or_domain: str, reason: Optional[str] = None) -> bool:
        """
        将域名添加到黑名单

        Args:
            url_or_domain: URL 或域名
            reason: 添加原因（可选）

        Returns:
            成功添加返回 True，如果已经在黑名单中返回 False
        """
        domain = self.get_domain_from_url(url_or_domain) if url_or_domain.startswith("http") else url_or_domain

        if not domain:
            logger.warning(f"无法从输入提取域名: {url_or_domain}")
            return False

        with self._lock:
            if domain in self._blacklist:
                logger.debug(f"域名已在黑名单中: {domain}")
                # 更新元数据
                if domain in self._blacklist_metadata:
                    self._blacklist_metadata[domain]["fail_count"] += 1
                    self._blacklist_metadata[domain]["last_failed"] = datetime.now().isoformat()
                    if reason:
                        self._blacklist_metadata[domain]["reason"] = reason
                return False

            self._blacklist.add(domain)
            self._blacklist_metadata[domain] = {
                "added_at": datetime.now().isoformat(),
                "fail_count": 1,
                "last_failed": datetime.now().isoformat(),
                "reason": reason or "Unknown"
            }
            logger.info(f"✅ 域名已添加到黑名单: {domain} (原因: {reason or 'Unknown'})")
            return True

    def remove_from_blacklist(self, url_or_domain: str) -> bool:
        """
        从黑名单中移除域名

        Args:
            url_or_domain: URL 或域名

        Returns:
            成功移除返回 True，如果不在黑名单中返回 False
        """
        domain = self.get_domain_from_url(url_or_domain) if url_or_domain.startswith("http") else url_or_domain

        if not domain:
            logger.warning(f"无法从输入提取域名: {url_or_domain}")
            return False

        with self._lock:
            if domain not in self._blacklist:
                logger.debug(f"域名不在黑名单中: {domain}")
                return False

            self._blacklist.remove(domain)
            self._blacklist_metadata.pop(domain, None)
            logger.info(f"域名已从黑名单移除: {domain}")
            return True

    def get_blacklist(self) -> Set[str]:
        """
        获取黑名单

        Returns:
            黑名单集合
        """
        with self._lock:
            return self._blacklist.copy()

    def get_blacklist_metadata(self) -> dict:
        """
        获取黑名单元数据

        Returns:
            黑名单元数据字典
        """
        with self._lock:
            return self._blacklist_metadata.copy()

    def clear_blacklist(self) -> None:
        """清空黑名单"""
        with self._lock:
            count = len(self._blacklist)
            self._blacklist.clear()
            self._blacklist_metadata.clear()
            logger.info(f"黑名单已清空，移除了 {count} 个域名")

    def cleanup_old_entries(self, days: int = 30) -> int:
        """
        清理旧的黑名单条目

        Args:
            days: 保留天数，超过此天数的条目将被移除

        Returns:
            移除的条目数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        with self._lock:
            domains_to_remove = []
            for domain, metadata in self._blacklist_metadata.items():
                added_at = datetime.fromisoformat(metadata["added_at"])
                if added_at < cutoff_date:
                    domains_to_remove.append(domain)

            for domain in domains_to_remove:
                self._blacklist.remove(domain)
                self._blacklist_metadata.pop(domain)
                removed_count += 1

            if removed_count > 0:
                logger.info(f"清理了 {removed_count} 个超过 {days} 天的黑名单条目")

        return removed_count

    def to_dict(self) -> dict:
        """
        将黑名单转换为字典格式（用于持久化）

        Returns:
            字典格式的黑名单
        """
        return {
            "domains": list(self._blacklist),
            "metadata": self._blacklist_metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DomainBlacklist":
        """
        从字典创建黑名单实例

        Args:
            data: 字典格式的黑名单

        Returns:
            DomainBlacklist 实例
        """
        domains = set(data.get("domains", []))
        blacklist = cls(initial_blacklist=domains)
        blacklist._blacklist_metadata = data.get("metadata", {})
        logger.info(f"从字典加载黑名单，包含 {len(domains)} 个域名")
        return blacklist

    def __len__(self) -> int:
        """返回黑名单中的域名数量"""
        with self._lock:
            return len(self._blacklist)

    def __contains__(self, url_or_domain: str) -> bool:
        """支持 'in' 操作符"""
        return self.is_blacklisted(url_or_domain)

    def __repr__(self) -> str:
        return f"DomainBlacklist(count={len(self._blacklist)})"