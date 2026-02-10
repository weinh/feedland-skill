"""OPML 解析模块"""

import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class FeedInfo:
    """Feed 信息"""

    url: str
    title: str
    feed_type: str


class OPMLParser:
    """OPML 解析器"""

    def __init__(self, timeout: int = 10):
        """
        初始化 OPML 解析器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout

    def parse_opml(self, opml_url: str) -> List[FeedInfo]:
        """
        解析 OPML 文档

        Args:
            opml_url: OPML 文档 URL

        Returns:
            Feed 信息列表

        Raises:
            requests.RequestException: 网络请求失败
            ET.ParseError: XML 解析失败
        """
        try:
            # 下载 OPML 文档
            response = requests.get(opml_url, timeout=self.timeout)
            response.raise_for_status()

            # 解析 XML
            root = ET.fromstring(response.content)

            # 提取 feeds
            feeds = []
            for outline in root.findall(".//outline"):
                feed = self._parse_outline(outline)
                if feed:
                    feeds.append(feed)

            logger.info(f"成功解析 OPML，找到 {len(feeds)} 个 feeds")
            return feeds

        except requests.RequestException as e:
            logger.error(f"下载 OPML 失败: {e}")
            raise
        except ET.ParseError as e:
            logger.error(f"解析 OPML XML 失败: {e}")
            raise
        except Exception as e:
            logger.error(f"解析 OPML 时发生错误: {e}")
            raise

    def _parse_outline(self, outline: ET.Element) -> Optional[FeedInfo]:
        """
        解析单个 outline 元素

        Args:
            outline: outline 元素

        Returns:
            Feed 信息，如果不是 feed 则返回 None
        """
        # 检查是否是 feed（有 xmlUrl 或 htmlUrl 属性）
        xml_url = outline.get("xmlUrl")
        if not xml_url:
            return None

        # 获取标题，如果没有则使用 URL 作为备用
        title = outline.get("title")
        if not title:
            title = outline.get("text")
        if not title:
            title = xml_url

        # 判断 feed 类型
        feed_type = self._detect_feed_type(xml_url, outline)

        return FeedInfo(url=xml_url, title=title, feed_type=feed_type)

    def _detect_feed_type(self, url: str, outline: ET.Element) -> str:
        """
        检测 feed 类型

        Args:
            url: feed URL
            outline: outline 元素

        Returns:
            feed 类型（RSS 或 Atom）
        """
        # 检查是否有 type 属性
        feed_type = outline.get("type", "")
        if feed_type:
            return feed_type.upper()

        # 根据 URL 判断
        url_lower = url.lower()
        if "atom" in url_lower or url_lower.endswith(".atom"):
            return "ATOM"

        # 默认为 RSS
        return "RSS"