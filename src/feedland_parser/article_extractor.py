"""文章内容提取模块"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from dateutil import parser as date_parser

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ArticleContent:
    """文章内容"""

    title: str
    url: str
    published: Optional[str]
    author: Optional[str]
    content: str
    success: bool = True


class ArticleExtractor:
    """文章内容提取器"""

    def __init__(self, timeout: int = 10, blacklist=None):
        """
        初始化文章提取器

        Args:
            timeout: 请求超时时间（秒）
            blacklist: 域名黑名单实例（可选）
        """
        self.timeout = timeout
        self.blacklist = blacklist

    def extract(self, article_url: str, title: Optional[str] = None,
                published: Optional[str] = None, author: Optional[str] = None,
                description: Optional[str] = None) -> ArticleContent:
        """
        提取文章内容

        优先使用 Newspaper3k，失败时回退到 BeautifulSoup，最后回退到描述内容

        Args:
            article_url: 文章 URL
            title: 文章标题（来自 feed）
            published: 发布日期（来自 feed）
            author: 作者（来自 feed）
            description: 描述内容（来自 feed，作为最后的回退）

        Returns:
            文章内容
        """
        # 检查域名黑名单
        if self.blacklist is not None and self.blacklist.is_blacklisted(article_url):
            domain = self.blacklist.get_domain_from_url(article_url)
            logger.info(f"⏭️  域名在黑名单中，直接使用描述内容: {domain} ({article_url})")
            
            # 直接使用描述内容，不再尝试提取 URL
            if description and len(description) >= 50:
                # 验证描述内容是否有效
                if self._is_content_valid(description):
                    logger.info(f"✅ 使用描述内容 ({len(description)} 字符): {article_url}")
                    return ArticleContent(
                        title=title or "Unknown",
                        url=article_url,
                        published=self._parse_timestamp(published),
                        author=author or "Unknown",
                        content=description,
                        success=True
                    )
                else:
                    logger.error(f"❌ 域名在黑名单中但描述内容包含乱码: {domain} ({article_url})")
                    return ArticleContent(
                        title=title or "Unknown",
                        url=article_url,
                        published=self._parse_timestamp(published),
                        author=author or "Unknown",
                        content="",
                        success=False
                    )
            else:
                logger.warning(f"⏭️  域名在黑名单中但无有效描述，跳过: {domain} ({article_url})")
                return ArticleContent(
                    title=title or "Unknown",
                    url=article_url,
                    published=self._parse_timestamp(published),
                    author=author or "Unknown",
                    content="",
                    success=False
                )

        logger.info(f"开始提取文章内容: {article_url}")
        
        try:
            # 首先尝试使用 cloudscraper（如果可用）
            if CLOUDSCRAPER_AVAILABLE:
                logger.debug(f"尝试使用 cloudscraper 提取: {article_url}")
                content = self.extract_with_cloudscraper(article_url, title)
                
                if content and len(content) >= 100:
                    # 验证内容是否有效（无乱码）
                    if not self._is_content_valid(content):
                        logger.error(f"❌ cloudscraper 提取的内容包含乱码: {article_url}")
                        # 内容无效，继续尝试其他方法
                    else:
                        logger.info(f"✅ cloudscraper 提取成功 ({len(content)} 字符): {article_url}")
                        return ArticleContent(
                            title=title or "Unknown",
                            url=article_url,
                            published=self._parse_timestamp(published),
                            author=author or "Unknown",
                            content=content,
                            success=True
                        )
                else:
                    logger.warning(f"cloudscraper 提取内容不足 ({len(content) if content else 0} 字符)，尝试 Newspaper3k: {article_url}")
            
            # cloudscraper 不可用或失败，尝试使用 Newspaper3k
            logger.debug(f"尝试使用 Newspaper3k 提取: {article_url}")
            article = None
            content = self.extract_with_newspaper3k(article_url, title, published, author)

            # 如果 Newspaper3k 提取失败，使用 BeautifulSoup 回退
            if not content or len(content) < 100:
                warning_msg = f"Newspaper3k 提取内容不足 ({len(content) if content else 0} 字符)"
                logger.warning(f"{warning_msg}，使用 BeautifulSoup 回退: {article_url}")
                if article:
                    logger.debug(f"Newspaper3k 提取详情: title={len(article.title) if article.title else 0}, text={len(article.text) if article.text else 0}")
                
                logger.debug(f"尝试使用 BeautifulSoup 提取: {article_url}")
                content = self.extract_with_beautifulsoup(article_url, title)
                
                if content:
                    # 验证内容是否有效（无乱码）
                    if self._is_content_valid(content):
                        logger.info(f"✅ BeautifulSoup 回退成功，提取了 {len(content)} 字符: {article_url}")
                    else:
                        logger.error(f"❌ BeautifulSoup 提取的内容包含乱码: {article_url}")
                        content = None
                else:
                    logger.error(f"❌ BeautifulSoup 回退也失败，无法提取内容: {article_url}")

            if content and len(content) >= 100:
                # 再次验证内容是否有效
                if not self._is_content_valid(content):
                    logger.error(f"❌ 最终提取的内容包含乱码: {article_url}")
                    content = None
                
                if content:
                    logger.info(f"✅ 文章内容提取成功 ({len(content)} 字符): {article_url}")
                    return ArticleContent(
                        title=title or "Unknown",
                        url=article_url,
                        published=self._parse_timestamp(published),
                        author=author or "Unknown",
                        content=content,
                    success=True
                )
            else:
                logger.error(f"❌ 文章内容提取失败 (内容不足: {len(content) if content else 0} 字符): {article_url}")
                
                # 尝试使用描述内容作为回退
                if description and len(description) >= 50:
                    # 验证描述内容是否有效
                    if self._is_content_valid(description):
                        logger.info(f"✅ 使用描述内容作为回退 ({len(description)} 字符): {article_url}")
                        # 添加到黑名单（因为 URL 提取失败）
                        if self.blacklist is not None:
                            self.blacklist.add_to_blacklist(article_url, reason="URL提取失败，使用描述内容回退")
                        return ArticleContent(
                            title=title or "Unknown",
                            url=article_url,
                            published=self._parse_timestamp(published),
                            author=author or "Unknown",
                            content=description,
                            success=True
                        )
                    else:
                        logger.error(f"❌ 描述内容包含乱码: {article_url}")
                
                # URL 提取失败且没有描述内容，添加到黑名单
                if self.blacklist is not None:
                    self.blacklist.add_to_blacklist(article_url, reason="URL提取失败且无描述内容")
                return ArticleContent(
                    title=title or "Unknown",
                    url=article_url,
                    published=self._parse_timestamp(published),
                    author=author or "Unknown",
                    content=content or "",
                    success=False
                )

        except Exception as e:
            logger.error(f"❌ 提取文章内容时发生异常: {article_url}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常详情: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # 尝试使用描述内容作为回退
            if description and len(description) >= 50:
                # 验证描述内容是否有效
                if self._is_content_valid(description):
                    logger.info(f"✅ 使用描述内容作为回退 ({len(description)} 字符): {article_url}")
                    return ArticleContent(
                        title=title or "Unknown",
                        url=article_url,
                        published=self._parse_timestamp(published),
                        author=author or "Unknown",
                        content=description,
                        success=True
                    )
                else:
                    logger.error(f"❌ 异常后描述内容包含乱码: {article_url}")
            
            # 只有当异常且没有描述内容时，才添加到黑名单
            if self.blacklist is not None:
                self.blacklist.add_to_blacklist(article_url, reason=f"提取异常且无描述内容: {type(e).__name__}")
            return ArticleContent(
                title=title or "Unknown",
                url=article_url,
                published=self._parse_timestamp(published),
                author=author or "Unknown",
                content="",
                success=False
            )

    def extract_with_cloudscraper(self, url: str, title: Optional[str] = None) -> Optional[str]:
        """
        使用 cloudscraper 提取文章内容（首选方案，可绕过 Cloudflare 保护）

        Args:
            url: 文章 URL
            title: 文章标题

        Returns:
            文章内容，提取失败返回 None
        """
        try:
            logger.debug(f"cloudscraper: 开始下载 {url}")
            
            # 创建 cloudscraper 实例
            scraper = cloudscraper.create_scraper()
            
            # 发送请求
            response = scraper.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            logger.debug(f"cloudscraper: HTTP {response.status_code}, 内容长度: {len(response.content)}")
            soup = BeautifulSoup(response.content, "lxml")

            # 尝试查找文章内容
            content = None

            # 查找常见的文章容器
            selectors = [
                "article",
                "main",
                "[role='main']",
                ".article-content",
                ".post-content",
                ".entry-content",
                ".content",
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    # 移除脚本和样式
                    for script in element(["script", "style"]):
                        script.decompose()
                    content = element.get_text(separator="\n", strip=True)
                    if len(content) > 100:
                        logger.debug(f"cloudscraper: 在选择器 '{selector}' 中找到内容 ({len(content)} 字符)")
                        break

            # 如果没有找到，尝试获取整个 body
            if not content or len(content) < 100:
                logger.debug(f"cloudscraper: 未找到文章容器，尝试获取整个 body")
                body = soup.find("body")
                if body:
                    for script in body(["script", "style"]):
                        script.decompose()
                    content = body.get_text(separator="\n", strip=True)
                    logger.debug(f"cloudscraper: body 内容长度: {len(content)} 字符")

            if content and len(content) > 100:
                return content

            logger.warning(f"cloudscraper 提取失败，内容不足: {len(content) if content else 0} 字符")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"cloudscraper: 请求超时: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"cloudscraper: HTTP 错误 {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"cloudscraper 提取失败: {e}")
            logger.debug(f"cloudscraper 异常类型: {type(e).__name__}")
            return None

    def extract_with_newspaper3k(self, url: str, title: Optional[str] = None,
                                  published: Optional[str] = None, author: Optional[str] = None) -> Optional[str]:
        """
        使用 Newspaper3k 提取文章内容

        Args:
            url: 文章 URL
            title: 文章标题（来自 feed）
            published: 发布日期（来自 feed）
            author: 作者（来自 feed）

        Returns:
            文章内容，提取失败返回 None
        """
        article = None
        try:
            logger.debug(f"Newspaper3k: 开始下载 {url}")
            article = Article(url, timeout=self.timeout)
            # 设置浏览器风格的 User-Agent 以绕过 Cloudflare 检测
            article.config.browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            article.download()
            
            logger.debug(f"Newspaper3k: 下载完成，开始解析")
            article.parse()

            content = article.text
            title_extracted = article.title
            authors_extracted = article.authors
            publish_date_extracted = article.publish_date

            logger.debug(f"Newspaper3k 提取详情: "
                        f"title={len(title_extracted) if title_extracted else 0}, "
                        f"authors={len(authors_extracted) if authors_extracted else 0}, "
                        f"text={len(content) if content else 0}")

            # 如果内容为空或太短，返回 None
            if not content or len(content) < 100:
                logger.warning(f"Newspaper3k 提取的内容不足: {len(content) if content else 0} 字符")
                if not content:
                    logger.warning(f"Newspaper3k: article.text 为空")
                return None

            return content

        except Exception as e:
            logger.warning(f"Newspaper3k 提取失败: {e}")
            logger.debug(f"Newspaper3k 异常类型: {type(e).__name__}")
            return None

    def extract_with_beautifulsoup(self, url: str, title: Optional[str] = None) -> Optional[str]:
        """
        使用 BeautifulSoup 提取文章内容（回退方案）

        Args:
            url: 文章 URL
            title: 文章标题

        Returns:
            文章内容，提取失败返回 None
        """
        try:
            logger.debug(f"BeautifulSoup: 开始下载 {url}")
            # 使用浏览器风格的请求头以绕过 Cloudflare 检测
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            
            logger.debug(f"BeautifulSoup: HTTP {response.status_code}, 内容长度: {len(response.content)}")
            soup = BeautifulSoup(response.content, "lxml")

            # 尝试查找文章内容
            content = None

            # 查找常见的文章容器
            selectors = [
                "article",
                "main",
                "[role='main']",
                ".article-content",
                ".post-content",
                ".entry-content",
                ".content",
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    # 移除脚本和样式
                    for script in element(["script", "style"]):
                        script.decompose()
                    content = element.get_text(separator="\n", strip=True)
                    if len(content) > 100:
                        logger.debug(f"BeautifulSoup: 在选择器 '{selector}' 中找到内容 ({len(content)} 字符)")
                        break

            # 如果没有找到，尝试获取整个 body
            if not content or len(content) < 100:
                logger.debug(f"BeautifulSoup: 未找到文章容器，尝试获取整个 body")
                body = soup.find("body")
                if body:
                    for script in body(["script", "style"]):
                        script.decompose()
                    content = body.get_text(separator="\n", strip=True)
                    logger.debug(f"BeautifulSoup: body 内容长度: {len(content)} 字符")

            if content and len(content) > 100:
                return content

            logger.warning(f"BeautifulSoup 提取失败，内容不足: {len(content) if content else 0} 字符")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"BeautifulSoup: 请求超时: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"BeautifulSoup: HTTP 错误 {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"BeautifulSoup 提取失败: {e}")
            logger.debug(f"BeautifulSoup 异常类型: {type(e).__name__}")
            return None

    def _is_content_valid(self, content: str) -> bool:
        """
        检查内容是否有效（不包含乱码）

        Args:
            content: 要检查的内容

        Returns:
            内容是否有效
        """
        if not content:
            return False
        
        # 检查内容长度
        if len(content) < 50:
            return False
        
        # 检查不可打印字符的比例
        total_chars = len(content)
        non_printable = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
        
        # 如果不可打印字符超过 10%，认为是乱码
        if non_printable / total_chars > 0.1:
            logger.warning(f"内容包含大量不可打印字符 ({non_printable}/{total_chars})，可能是乱码")
            return False
        
        # 检查是否包含大量的控制字符或特殊字符
        # 如果内容中包含太多的 null 字符或其他控制字符，认为是乱码
        null_count = content.count('\x00')
        if null_count > 0:
            logger.warning(f"内容包含 {null_count} 个 null 字符，可能是乱码")
            return False
        
        # 检查内容是否全是 ASCII 范围但不是英文（可能是编码错误）
        # 如果内容包含大量 0x80-0xFF 范围的字符，但不是有效的 UTF-8，认为是乱码
        try:
            # 尝试重新编码和解码以验证编码正确性
            content.encode('utf-8').decode('utf-8')
        except UnicodeError as e:
            logger.warning(f"内容编码验证失败: {e}")
            return False
        
        return True

    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """
        解析时间戳，支持多种格式

        Args:
            timestamp: 时间戳字符串

        Returns:
            ISO 8601 格式的时间戳，解析失败返回 None
        """
        if not timestamp:
            return None

        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(timestamp)
            return dt.isoformat()
        except Exception as e:
            logger.debug(f"解析时间戳失败: {e}")
            return None
        
        # 检查是否包含大量的控制字符或特殊字符
        # 如果内容中包含太多的 null 字符或其他控制字符，认为是乱码
        null_count = content.count('\x00')
        if null_count > 0:
            logger.warning(f"内容包含 {null_count} 个 null 字符，可能是乱码")
            return False
        
        # 检查内容是否全是 ASCII 范围但不是英文（可能是编码错误）
        # 如果内容包含大量 0x80-0xFF 范围的字符，但不是有效的 UTF-8，认为是乱码
        try:
            # 尝试重新编码和解码以验证编码正确性
            content.encode('utf-8').decode('utf-8')
        except UnicodeError as e:
            logger.warning(f"内容编码验证失败: {e}")
            return False
        
        return True
        """
        解析时间戳，支持多种格式

        Args:
            timestamp: 时间戳字符串

        Returns:
            ISO 8601 格式的时间戳，解析失败返回 None
        """
        if not timestamp:
            return None

        try:
            dt = date_parser.parse(timestamp)
            return dt.isoformat()
        except Exception as e:
            logger.debug(f"解析时间戳失败: {e}")
            return None

    def extract_metadata(self, article_url: str) -> Dict[str, Any]:
        """
        提取文章元数据

        Args:
            article_url: 文章 URL

        Returns:
            元数据字典
        """
        try:
            article = Article(article_url, timeout=self.timeout)
            article.download()
            article.parse()

            return {
                "title": article.title,
                "url": article_url,
                "published": self._parse_timestamp(article.publish_date.isoformat() if article.publish_date else None),
                "author": article.authors[0] if article.authors else None,
            }
        except Exception as e:
            logger.error(f"提取文章元数据失败: {e}")
            return {
                "title": "Unknown",
                "url": article_url,
                "published": None,
                "author": None,
            }
