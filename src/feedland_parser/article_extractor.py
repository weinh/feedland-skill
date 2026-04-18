"""文章内容提取模块

提取策略（按优先级）：
1. Readability 算法（智能正文提取）
2. Newspaper3k（NLP 分析）
3. CSS 选择器（兜底）
4. 描述内容（最终回退）

网络错误检测：当检测到网络错误时，立即停止后续尝试，直接使用描述内容。
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from dateutil import parser as date_parser
from readability.readability import Unparseable
from readability import Document as ReadabilityDocument

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# 类型定义
# ============================================================================

class NetworkError(Exception):
    """网络错误异常（超时、连接失败等）"""
    pass


@dataclass
class ArticleContent:
    """文章内容"""
    title: str
    url: str
    published: Optional[str]
    author: Optional[str]
    content: str
    images: List[str] = None
    success: bool = True
    extraction_method: Optional[str] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []


# ============================================================================
# 常量定义
# ============================================================================

# 图片选择器（按优先级）
IMAGE_SELECTORS = [
    "article img", "main img", ".article-content img", ".article-body img",
    ".article__body img", ".post-content img", ".post-body img", ".entry-content img",
    ".story-body img", ".blog-post img", ".single-content img", "[itemprop='image'] img",
    "[class*='article'] img", "[class*='post'] img", "figure img",
    ".featured-image img", ".cover-image img",
]

# CSS 选择器兜底列表（按优先级）
CSS_SELECTORS = [
    "article", "main", "[role='main']",
    "[itemprop='articleBody']", "[itemprop='text']",
    ".article-content", ".article-body", ".article__body", ".article-text",
    ".post-content", ".post-body", ".post-text", ".entry-content", ".entry-body",
    ".story-body", ".story-content", ".blog-post-content", ".single-content",
    ".single-post", ".content-body", ".content",
    "#article-body", "#post-body", "#content-body", "#main-content",
    "[data-component='article-body']", "[data-content='article']",
    "[data-testid='article-body']",
    ".wp-block-post-content", ".elementor-theme-builder-content",
    "[class*='article-body']", "[class*='post-content']",
]


# ============================================================================
# 工具函数
# ============================================================================

def _clean_text(text: str) -> str:
    """清理文本：移除多余空行和空白"""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)


def _is_content_valid(content: str) -> bool:
    """检查内容是否有效"""
    if not content or len(content) < 50:
        return False

    total_chars = len(content)
    non_printable = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
    if non_printable / total_chars > 0.1:
        return False
    if '\x00' in content:
        return False

    try:
        content.encode('utf-8').decode('utf-8')
    except UnicodeError:
        return False
    return True


def _parse_timestamp(timestamp: Optional[str]) -> Optional[str]:
    """解析时间戳为 ISO 8601 格式"""
    if not timestamp:
        return None
    try:
        dt = date_parser.parse(timestamp)
        return dt.isoformat()
    except Exception:
        return None


# ============================================================================
# 提取策略基类
# ============================================================================

class ExtractionStrategy:
    """提取策略基类"""

    name: str = ""
    timeout: tuple = (3, 10)

    def extract(self, url: str, session: requests.Session) -> Optional[str]:
        raise NotImplementedError

    def _get_html(self, url: str, session: requests.Session, use_cloudscraper: bool = False) -> Optional[str]:
        """获取 HTML 内容"""
        try:
            if use_cloudscraper:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=self.timeout)
            else:
                response = session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # 修复编码检测问题：使用 apparent_encoding 而不是默认的 ISO-8859-1
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'

            return response.text
        except requests.exceptions.Timeout:
            raise NetworkError(f"{self.name} 请求超时")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"{self.name} 连接失败: {e}")
        except requests.exceptions.HTTPError:
            return None
        except Exception:
            return None

    def _html_to_text(self, html: str) -> Optional[str]:
        """HTML 转纯文本"""
        if not html:
            return None
        try:
            soup = BeautifulSoup(html, "lxml")
            doc = ReadabilityDocument(html)
            content = doc.summary()
            if not content:
                return None
            soup = BeautifulSoup(content, "lxml")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return _clean_text(text) if len(text) >= 100 else None
        except Unparseable:
            return None
        except Exception:
            return None


class ReadabilityStrategy(ExtractionStrategy):
    """Readability 算法提取"""

    name = "Readability"

    def extract(self, url: str, session: requests.Session) -> Optional[str]:
        html = self._get_html(url, session)
        return self._html_to_text(html)


class CloudscraperStrategy(ExtractionStrategy):
    """cloudscraper + Readability 提取"""

    name = "cloudscraper+Readability"

    def extract(self, url: str, session: requests.Session) -> Optional[str]:
        if not CLOUDSCRAPER_AVAILABLE:
            return None
        html = self._get_html(url, session, use_cloudscraper=True)
        return self._html_to_text(html)


class NewspaperStrategy(ExtractionStrategy):
    """Newspaper3k 提取"""

    name = "Newspaper3k"

    def extract(self, url: str, session: requests.Session) -> Optional[str]:
        try:
            article = Article(url, timeout=10)
            article.download()
            article.parse()
            content = article.text
            return _clean_text(content) if content and len(content) >= 100 else None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NetworkError(f"Newspaper3k {e}")
        except Exception:
            return None


class CSSSelectorStrategy(ExtractionStrategy):
    """CSS 选择器提取"""

    name = "CSS-Selectors"

    def extract(self, url: str, session: requests.Session) -> Optional[str]:
        try:
            response = session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "lxml")

            # 尝试各选择器
            for selector in CSS_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    best = max(elements, key=lambda e: len(e.get_text()))
                    for script in best(["script", "style"]):
                        script.decompose()
                    text = best.get_text(separator="\n", strip=True)
                    if len(text) >= 100:
                        return _clean_text(text)

            # 兜底：使用 body
            body = soup.find("body")
            if body:
                for script in body(["script", "style"]):
                    script.decompose()
                return _clean_text(body.get_text(separator="\n", strip=True))
            return None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NetworkError(f"CSS-Selectors {e}")
        except Exception:
            return None


# ============================================================================
# 主提取器
# ============================================================================

class ArticleExtractor:
    """文章内容提取器"""

    def __init__(self, timeout: int = 10, blacklist=None, connect_timeout: int = 3):
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self._timeout = (connect_timeout, timeout)
        self.blacklist = blacklist
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        # 提取策略列表（按优先级）
        self._strategies: List[ExtractionStrategy] = [
            ReadabilityStrategy(),
            CloudscraperStrategy(),
            NewspaperStrategy(),
            CSSSelectorStrategy(),
        ]

    def close(self):
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        self.close()

    # -------------------------------------------------------------------------
    # 主提取逻辑
    # -------------------------------------------------------------------------

    def extract(self, article_url: str, title: Optional[str] = None,
                published: Optional[str] = None, author: Optional[str] = None,
                description: Optional[str] = None, feed_name: Optional[str] = None) -> ArticleContent:
        """提取文章内容"""

        # 检查黑名单
        if self.blacklist and self.blacklist.is_blacklisted(article_url):
            domain = self.blacklist.get_domain_from_url(article_url)
            logger.info(f"⏭️  域名在黑名单中: {domain}")
            return self._fallback(article_url, title, published, author, description, "域名在黑名单中", feed_name)

        logger.info(f"开始提取: {article_url}")

        # 尝试各提取策略
        for strategy in self._strategies:
            try:
                logger.debug(f"尝试 {strategy.name}: {article_url}")
                content = strategy.extract(article_url, self._session)

                if content and len(content) >= 100 and _is_content_valid(content):
                    images = self._extract_images(article_url)
                    logger.info(f"✅ {strategy.name} 成功 ({len(content)} 字符)")
                    return ArticleContent(
                        title=title or "Unknown",
                        url=article_url,
                        published=_parse_timestamp(published),
                        author=author or "Unknown",
                        content=content,
                        images=images,
                        success=True,
                        extraction_method=strategy.name.lower().replace("+", "-")
                    )
            except NetworkError as e:
                feed_display = feed_name or "Unknown"
                logger.warning(f"⚠️ {strategy.name} 网络错误: {article_url} - {feed_display} - {e}")
                # 网络错误立即停止
                return self._fallback(article_url, title, published, author, description, f"网络错误: {e}", feed_name)
            except Exception as e:
                logger.debug(f"❌ {strategy.name} 失败: {e}")

        # 全部失败，使用描述回退
        feed_display = feed_name or "Unknown"
        logger.error(f"❌ 所有提取方法失败: {article_url} - {feed_display}")
        return self._fallback(article_url, title, published, author, description, "所有提取方法失败", feed_name)

    def _fallback(self, article_url: str, title: Optional[str], published: Optional[str],
                  author: Optional[str], description: Optional[str], reason: str,
                  feed_name: Optional[str] = None) -> ArticleContent:
        """描述内容回退"""
        is_network_error = reason and reason.startswith("网络错误")

        if description and len(description) >= 50 and _is_content_valid(description):
            logger.info(f"✅ 描述回退 ({len(description)} 字符)")

            if is_network_error and self.blacklist:
                self.blacklist.add_to_blacklist(article_url, reason=reason)
                logger.info(f"🚫 加入黑名单: {article_url}")

            return ArticleContent(
                title=title or "Unknown",
                url=article_url,
                published=_parse_timestamp(published),
                author=author or "Unknown",
                content=description,
                success=True,
                extraction_method="description-fallback"
            )

        if is_network_error and self.blacklist:
            self.blacklist.add_to_blacklist(article_url, reason=f"{reason}，且无有效描述")

        return ArticleContent(
            title=title or "Unknown",
            url=article_url,
            published=_parse_timestamp(published),
            author=author or "Unknown",
            content="",
            success=False,
            extraction_method="failed"
        )

    # -------------------------------------------------------------------------
    # 图片提取
    # -------------------------------------------------------------------------

    def _extract_images(self, url: str, max_images: int = 10) -> List[str]:
        """提取文章中的图片 URL"""
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "lxml")

            images = []
            seen = set()

            # 策略 1: article 标签
            article = soup.find("article")
            if article:
                for img in article.find_all("img"):
                    src = self._get_image_src(img)
                    if src and self._is_valid_image(src, img):
                        absolute = urljoin(url, src)
                        if absolute not in seen:
                            seen.add(absolute)
                            images.append(absolute)

            # 策略 2: readability-content
            if len(images) < 3:
                rc = soup.find("div", {"id": "readability-content"})
                if rc:
                    for img in rc.find_all("img"):
                        src = self._get_image_src(img)
                        if src and self._is_valid_image(src, img):
                            absolute = urljoin(url, src)
                            if absolute not in seen:
                                seen.add(absolute)
                                images.append(absolute)

            # 策略 3: 选择器
            if len(images) < 3:
                for selector in IMAGE_SELECTORS:
                    for elem in soup.select(selector):
                        img = elem if elem.name == "img" else elem.find("img")
                        if img:
                            src = self._get_image_src(img)
                            if src and self._is_valid_image(src, img):
                                absolute = urljoin(url, src)
                                if absolute not in seen:
                                    seen.add(absolute)
                                    images.append(absolute)

            return images[:max_images]

        except Exception as e:
            logger.warning(f"📷 图片提取失败: {e}")
            return []

    def _get_image_src(self, img) -> Optional[str]:
        """从 img 标签获取 URL"""
        if not img:
            return None

        # 懒加载
        for attr in ["data-src", "data-lazy-src", "data-original"]:
            if img.get(attr):
                return img.get(attr)

        # 标准 src
        src = img.get("src")
        if src and not src.startswith("data:"):
            return src

        # srcset
        srcset = img.get("srcset")
        if srcset:
            return srcset.split(",")[0].split()[0]
        return None

    def _is_valid_image(self, url: str, img) -> bool:
        """检查图片是否有效"""
        if not url or not url.startswith("http"):
            return False

        # 过滤追踪域名
        skip_domains = ["googletagmanager", "google-analytics", "facebook.net",
                        "analytics", "tracking", "pixel", "beacon", "adsystem"]
        if any(d in url.lower() for d in skip_domains):
            return False

        # 过滤小图
        try:
            w = int(img.get("width", 0))
            h = int(img.get("height", 0))
            if w and h and (w < 100 or h < 100):
                return False
        except (ValueError, TypeError):
            pass

        # 过滤 skip 关键词
        skip_patterns = ["icon", "logo", "avatar", "user-pic", "profile", "button", "btn"]
        if any(p in url.lower() for p in skip_patterns):
            return False

        return True

    # -------------------------------------------------------------------------
    # 元数据
    # -------------------------------------------------------------------------

    def extract_metadata(self, article_url: str) -> Dict[str, Any]:
        """提取文章元数据"""
        try:
            article = Article(article_url, timeout=self.timeout)
            article.download()
            article.parse()
            return {
                "title": article.title,
                "url": article_url,
                "published": _parse_timestamp(article.publish_date.isoformat() if article.publish_date else None),
                "author": article.authors[0] if article.authors else None,
            }
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            return {"title": "Unknown", "url": article_url, "published": None, "author": None}
