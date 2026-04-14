"""文章内容提取模块 - 优化版

提取策略（按优先级）：
1. Readability 算法（智能正文提取）
2. Newspaper3k（NLP 分析）
3. CSS 选择器（兜底）
4. 描述内容（最终回退）

网络错误检测：当检测到网络错误时，立即停止后续尝试，直接使用描述内容。
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
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
    images: List[str] = None  # 文章中的图片 URL 列表
    success: bool = True
    extraction_method: Optional[str] = None  # 记录使用的提取方法

    def __post_init__(self):
        if self.images is None:
            self.images = []


class ArticleExtractor:
    """文章内容提取器 - 优化版"""

    # 图片选择器（按优先级）
    IMAGE_SELECTORS: List[str] = [
        "article img",
        "main img",
        ".article-content img",
        ".article-body img",
        ".article__body img",
        ".post-content img",
        ".post-body img",
        ".entry-content img",
        ".story-body img",
        ".blog-post img",
        ".single-content img",
        "[itemprop='image'] img",
        "[class*='article'] img",
        "[class*='post'] img",
        "figure img",
        ".featured-image img",
        ".cover-image img",
    ]

    # CSS 选择器兜底列表（按优先级）
    CSS_SELECTORS: List[str] = [
        # 语义化标签
        "article",
        "main",
        "[role='main']",
        # 微数据
        "[itemprop='articleBody']",
        "[itemprop='text']",
        # 常见正文类名
        ".article-content",
        ".article-body",
        ".article__body",
        ".article-text",
        ".post-content",
        ".post-body",
        ".post-text",
        ".entry-content",
        ".entry-body",
        ".story-body",
        ".story-content",
        ".blog-post-content",
        ".single-content",
        ".single-post",
        ".content-body",
        ".content",
        # ID 选择器
        "#article-body",
        "#post-body",
        "#content-body",
        "#main-content",
        # data 属性
        "[data-component='article-body']",
        "[data-content='article']",
        "[data-testid='article-body']",
        # 常见 CMS
        ".wp-block-post-content",
        ".elementor-theme-builder-content",
        "[class*='article-body']",
        "[class*='post-content']",
    ]

    def __init__(self, timeout: int = 10, blacklist=None, connect_timeout: int = 3):
        """
        初始化文章提取器

        Args:
            timeout: 读取超时时间（秒）
            blacklist: 域名黑名单实例（可选）
            connect_timeout: 连接超时时间（秒），默认 3 秒，比读取更快失败
        """
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        # 使用 tuple 超时: (connect_timeout, read_timeout)
        self._timeout = (connect_timeout, timeout)
        self.blacklist = blacklist
        # 创建 Session 用于连接池复用
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        })
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=1
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def close(self):
        """关闭 Session 释放资源"""
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

    def extract(self, article_url: str, title: Optional[str] = None,
                published: Optional[str] = None, author: Optional[str] = None,
                description: Optional[str] = None) -> ArticleContent:
        """
        提取文章内容（优化版提取顺序）

        提取顺序：
        1. Readability 算法（智能正文提取）
        2. Newspaper3k（NLP 分析）
        3. CSS 选择器（兜底）
        4. 描述内容（最终回退）

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
            return self._use_description_fallback(
                article_url, title, published, author, description, 
                reason="域名在黑名单中"
            )

        logger.info(f"开始提取文章内容: {article_url}")
        content = None
        extraction_method = None
        network_error = None  # 记录网络错误

        # ========== 方法 1: Readability 算法（首选）==========
        logger.debug(f"[1/4] 尝试 Readability 算法: {article_url}")
        try:
            content = self._extract_with_readability(article_url)
            if content and len(content) >= 100 and self._is_content_valid(content):
                extraction_method = "readability"
                logger.info(f"✅ Readability 成功 ({len(content)} 字符): {article_url}")
            else:
                logger.debug(f"❌ Readability 失败，内容: {len(content) if content else 0} 字符")
        except NetworkError as e:
            network_error = str(e)
            logger.warning(f"⚠️ Readability 网络错误，立即停止: {article_url} ({network_error})")

        # ========== 方法 2: cloudscraper + Readability（备选）==========
        if network_error is None and (not content or len(content) < 100 or not self._is_content_valid(content)):
            if CLOUDSCRAPER_AVAILABLE:
                logger.debug(f"[2/4] 尝试 cloudscraper + Readability: {article_url}")
                try:
                    content = self._extract_with_cloudscraper_readability(article_url)
                    if content and len(content) >= 100 and self._is_content_valid(content):
                        extraction_method = "cloudscraper+readability"
                        logger.info(f"✅ cloudscraper+Readability 成功 ({len(content)} 字符): {article_url}")
                except NetworkError as e:
                    network_error = str(e)
                    logger.warning(f"⚠️ cloudscraper 网络错误，立即停止: {article_url} ({network_error})")

        # ========== 方法 3: Newspaper3k ==========
        if network_error is None and (not content or len(content) < 100 or not self._is_content_valid(content)):
            logger.debug(f"[3/4] 尝试 Newspaper3k: {article_url}")
            try:
                content = self._extract_with_newspaper3k(article_url)
                if content and len(content) >= 100 and self._is_content_valid(content):
                    extraction_method = "newspaper3k"
                    logger.info(f"✅ Newspaper3k 成功 ({len(content)} 字符): {article_url}")
            except NetworkError as e:
                network_error = str(e)
                logger.warning(f"⚠️ Newspaper3k 网络错误，立即停止: {article_url} ({network_error})")

        # ========== 方法 4: CSS 选择器（兜底）==========
        if network_error is None and (not content or len(content) < 100 or not self._is_content_valid(content)):
            logger.debug(f"[4/4] 尝试 CSS 选择器: {article_url}")
            try:
                content = self._extract_with_css_selectors(article_url)
                if content and len(content) >= 100 and self._is_content_valid(content):
                    extraction_method = "css-selectors"
                    logger.info(f"✅ CSS 选择器成功 ({len(content)} 字符): {article_url}")
            except NetworkError as e:
                network_error = str(e)
                logger.warning(f"⚠️ CSS 选择器网络错误，立即停止: {article_url} ({network_error})")

        # ========== 成功返回 ==========
        if content and len(content) >= 100 and self._is_content_valid(content):
            # 提取图片
            images = self._extract_images(article_url)
            logger.info(f"📷 提取到 {len(images)} 张图片: {article_url}")

            return ArticleContent(
                title=title or "Unknown",
                url=article_url,
                published=self._parse_timestamp(published),
                author=author or "Unknown",
                content=content,
                images=images,
                success=True,
                extraction_method=extraction_method
            )

        # ========== 全部失败，使用描述内容回退 ==========
        if network_error:
            logger.warning(f"⚠️ 网络错误，使用描述内容回退: {article_url} ({network_error})")
            return self._use_description_fallback(
                article_url, title, published, author, description,
                reason=f"网络错误: {network_error}"
            )
        else:
            logger.error(f"❌ 所有提取方法失败，使用描述内容回退: {article_url}")
            return self._use_description_fallback(
                article_url, title, published, author, description,
                reason="所有提取方法失败"
            )

    def _extract_with_readability(self, url: str) -> Optional[str]:
        """
        使用 Readability 算法提取文章内容

        Readability 是 Mozilla 开发的智能正文提取算法，
        通过分析文本密度、标签权重等智能识别正文区域。

        Args:
            url: 文章 URL

        Returns:
            文章内容，提取失败返回 None
        """
        try:
            logger.debug(f"Readability: 下载 {url}")
            # 使用 Session 和分开的超时
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()

            # Readability 需要 string（文本），不是 bytes
            html_content = response.text

            # 使用 Readability 解析
            doc = ReadabilityDocument(html_content)
            title = doc.title()
            text_content = doc.summary()

            # Readability 返回的是 HTML，需要提取纯文本
            if text_content:
                soup = BeautifulSoup(text_content, "lxml")
                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()
                content = soup.get_text(separator="\n", strip=True)

                # 清理多余空行
                content = self._clean_text(content)

                logger.debug(f"Readability: 提取 {len(content)} 字符")
                return content if len(content) >= 100 else None

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Readability: 请求超时: {url}")
            raise NetworkError("Readability 请求超时")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Readability: 连接失败: {url}")
            raise NetworkError(f"Readability 连接失败: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Readability: HTTP 错误 {e.response.status_code}: {url}")
            # HTTP 错误不是网络问题，继续尝试其他方法
            return None
        except Unparseable:
            logger.warning(f"Readability: 无法解析页面: {url}")
            return None
        except Exception as e:
            logger.warning(f"Readability: 提取失败: {e}")
            return None

    def _extract_with_cloudscraper_readability(self, url: str) -> Optional[str]:
        """
        使用 cloudscraper + Readability 提取（可绕过 Cloudflare）

        Args:
            url: 文章 URL

        Returns:
            文章内容，提取失败返回 None
        """
        if not CLOUDSCRAPER_AVAILABLE:
            return None

        try:
            logger.debug(f"cloudscraper+Readability: 下载 {url}")
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=self._timeout)
            response.raise_for_status()

            # Readability 需要 string（文本）
            html_content = response.text

            # 使用 Readability 解析
            doc = ReadabilityDocument(html_content)
            text_content = doc.summary()

            if text_content:
                soup = BeautifulSoup(text_content, "lxml")
                for script in soup(["script", "style"]):
                    script.decompose()
                content = soup.get_text(separator="\n", strip=True)
                content = self._clean_text(content)

                logger.debug(f"cloudscraper+Readability: 提取 {len(content)} 字符")
                return content if len(content) >= 100 else None

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"cloudscraper+Readability: 请求超时: {url}")
            raise NetworkError("cloudscraper+Readability 请求超时")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"cloudscraper+Readability: 连接失败: {url}")
            raise NetworkError(f"cloudscraper+Readability 连接失败: {e}")
        except Unparseable:
            logger.warning(f"cloudscraper+Readability: 无法解析: {url}")
            return None
        except Exception as e:
            logger.warning(f"cloudscraper+Readability: 提取失败: {e}")
            return None

    def _extract_with_newspaper3k(self, url: str) -> Optional[str]:
        """
        使用 Newspaper3k 提取文章内容

        Args:
            url: 文章 URL

        Returns:
            文章内容，提取失败返回 None
        """
        try:
            logger.debug(f"Newspaper3k: 下载 {url}")
            # newspaper3k 的 timeout 参数是总超时，我们传入读取超时
            article = Article(url, timeout=self.timeout)
            article.config.browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            article.download()
            article.parse()

            content = article.text
            if content and len(content) >= 100:
                content = self._clean_text(content)
                logger.debug(f"Newspaper3k: 提取 {len(content)} 字符")
                return content

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Newspaper3k: 请求超时: {url}")
            raise NetworkError("Newspaper3k 请求超时")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Newspaper3k: 连接失败: {url}")
            raise NetworkError(f"Newspaper3k 连接失败: {e}")
        except Exception as e:
            logger.warning(f"Newspaper3k: 提取失败: {e}")
            return None

    def _extract_with_css_selectors(self, url: str) -> Optional[str]:
        """
        使用 CSS 选择器提取文章内容（兜底方案）

        Args:
            url: 文章 URL

        Returns:
            文章内容，提取失败返回 None
        """
        try:
            logger.debug(f"CSS 选择器: 下载 {url}")
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            content = None

            # 按优先级尝试每个选择器
            for selector in self.CSS_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    # 优先选择最大的元素（内容最多）
                    best_element = max(elements, key=lambda e: len(e.get_text()))
                    for script in best_element(["script", "style"]):
                        script.decompose()
                    text = best_element.get_text(separator="\n", strip=True)

                    if len(text) >= 100:
                        content = self._clean_text(text)
                        logger.debug(f"CSS 选择器: '{selector}' 匹配成功，提取 {len(content)} 字符")
                        break

            # 如果选择器都没找到，使用 body
            if not content or len(content) < 100:
                logger.debug(f"CSS 选择器: 未找到匹配，尝试 body")
                body = soup.find("body")
                if body:
                    for script in body(["script", "style"]):
                        script.decompose()
                    content = self._clean_text(body.get_text(separator="\n", strip=True))
                    logger.debug(f"CSS 选择器: body 提取 {len(content) if content else 0} 字符")

            return content if content and len(content) >= 100 else None

        except requests.exceptions.Timeout:
            logger.error(f"CSS 选择器: 请求超时: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"CSS 选择器: HTTP 错误 {e.response.status_code}: {url}")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"CSS 选择器: 请求超时: {url}")
            raise NetworkError("CSS 选择器请求超时")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"CSS 选择器: 连接失败: {url}")
            raise NetworkError(f"CSS 选择器连接失败: {e}")
        except Exception as e:
            logger.error(f"CSS 选择器: 提取失败: {e}")
            return None

    def _extract_images(self, url: str, max_images: int = 10) -> List[str]:
        """
        提取文章中的图片 URL

        Args:
            url: 文章 URL（用于解析相对路径）
            max_images: 最大返回图片数量

        Returns:
            图片 URL 列表
        """
        from urllib.parse import urljoin

        try:
            logger.debug(f"📷 提取图片: {url}")
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            images = []
            seen_urls = set()  # 去重

            # 策略 1: 从 article 标签提取
            article = soup.find("article")
            if article:
                article_images = article.find_all("img")
                for img in article_images:
                    src = self._get_image_src(img)
                    if src and src not in seen_urls:
                        # 过滤小图标和追踪像素
                        if self._is_valid_image(src, img):
                            absolute_url = urljoin(url, src)
                            seen_urls.add(absolute_url)
                            images.append(absolute_url)

            # 策略 2: 从 Readability 提取区域提取
            readability_content = soup.find("div", {"id": "readability-content"})
            if readability_content:
                readability_images = readability_content.find_all("img")
                for img in readability_images:
                    src = self._get_image_src(img)
                    if src and src not in seen_urls:
                        if self._is_valid_image(src, img):
                            absolute_url = urljoin(url, src)
                            seen_urls.add(absolute_url)
                            images.append(absolute_url)

            # 策略 3: 使用图片选择器
            if len(images) < 3:
                for selector in self.IMAGE_SELECTORS:
                    elements = soup.select(selector)
                    for elem in elements:
                        if isinstance(elem, type(soup.find("img"))):  # img 标签
                            src = self._get_image_src(elem)
                        else:
                            src = self._get_image_src(elem.find("img"))
                        if src and src not in seen_urls:
                            if self._is_valid_image(src, elem if isinstance(elem, type(soup.find("img"))) else elem.find("img")):
                                absolute_url = urljoin(url, src)
                                seen_urls.add(absolute_url)
                                images.append(absolute_url)

            # 策略 4: 通用 img 标签提取（兜底）
            if len(images) < 3:
                all_images = soup.find_all("img")
                for img in all_images:
                    src = self._get_image_src(img)
                    if src and src not in seen_urls:
                        if self._is_valid_image(src, img):
                            absolute_url = urljoin(url, src)
                            seen_urls.add(absolute_url)
                            images.append(absolute_url)

            # 限制数量
            images = images[:max_images]
            logger.debug(f"📷 提取到 {len(images)} 张图片")

            return images

        except Exception as e:
            logger.warning(f"📷 图片提取失败: {e}")
            return []

    def _get_image_src(self, img) -> Optional[str]:
        """
        从 img 标签获取图片 URL

        优先顺序：data-src > src > srcset

        Args:
            img: BeautifulSoup img 标签

        Returns:
            图片 URL 或 None
        """
        if not img:
            return None

        # 优先 data-src（懒加载）
        if img.get("data-src"):
            return img.get("data-src")
        if img.get("data-lazy-src"):
            return img.get("data-lazy-src")
        if img.get("data-original"):
            return img.get("data-original")

        # 标准 src
        src = img.get("src")
        if src and not src.startswith("data:"):
            return src

        # srcset（取第一张）
        srcset = img.get("srcset")
        if srcset:
            # srcset 格式: "url1 size1, url2 size2, ..."
            first_url = srcset.split(",")[0].split()[0]
            if first_url and not first_url.startswith("data:"):
                return first_url

        return None

    def _is_valid_image(self, url: str, img) -> bool:
        """
        检查图片是否有效（过滤小图标、追踪像素等）

        Args:
            url: 图片 URL
            img: BeautifulSoup img 标签

        Returns:
            是否有效
        """
        if not url or not url.startswith("http"):
            return False

        # 检查是否是常见的小图标域名
        skip_domains = [
            "googletagmanager",
            "google-analytics",
            "facebook.net",
            "analytics",
            "tracking",
            "pixel",
            "beacon",
            "adsystem",
            "adservice",
            "doubleclick",
        ]
        url_lower = url.lower()
        if any(domain in url_lower for domain in skip_domains):
            return False

        # 检查 width/height 属性
        width = img.get("width")
        height = img.get("height")
        if width and height:
            try:
                w = int(width) if isinstance(width, str) else width
                h = int(height) if isinstance(height, str) else height
                # 过滤小于 100x100 的图片
                if w < 100 or h < 100:
                    return False
            except (ValueError, TypeError):
                pass

        # 检查 alt 文本是否包含 skip/ads
        alt = img.get("alt", "").lower()
        if any(skip in alt for skip in ["skip", "ad", "advertisement", "sponsor"]):
            return False

        # 检查 class 是否包含 skip
        classes = img.get("class", [])
        class_str = " ".join(classes).lower()
        if any(skip in class_str for skip in ["skip", "ad", "banner", "logo", "icon", "avatar"]):
            return False

        # 检查 URL 是否包含 skip 关键词
        skip_patterns = ["icon", "logo", "avatar", "avatar", "user-pic", "profile", "button", "btn"]
        if any(pattern in url_lower for pattern in skip_patterns):
            return False

        return True

    def _use_description_fallback(self, article_url: str, title: Optional[str],
                                  published: Optional[str], author: Optional[str],
                                  description: Optional[str], reason: str) -> ArticleContent:
        """
        使用描述内容作为回退

        Args:
            article_url: 文章 URL
            title: 标题
            published: 发布日期
            author: 作者
            description: 描述内容
            reason: 回退原因

        Returns:
            文章内容
        """
        # 只有网络错误才加入黑名单（下次大概率还不通，跳过省时）
        # 内容提取失败不拉黑（可能是临时页面问题，下次可能正常）
        is_network_error = reason and reason.startswith("网络错误")

        if description and len(description) >= 50 and self._is_content_valid(description):
            logger.info(f"✅ 使用描述内容回退 ({len(description)} 字符): {article_url}")

            if is_network_error and self.blacklist is not None:
                self.blacklist.add_to_blacklist(article_url, reason=reason)
                logger.info(f"🚫 网络错误，加入黑名单: {article_url}")

            return ArticleContent(
                title=title or "Unknown",
                url=article_url,
                published=self._parse_timestamp(published),
                author=author or "Unknown",
                content=description,
                success=True,
                extraction_method="description-fallback"
            )

        # 没有有效描述时，网络错误才拉黑
        if is_network_error and self.blacklist is not None:
            self.blacklist.add_to_blacklist(article_url, reason=f"{reason}，且无有效描述")
            logger.info(f"🚫 网络错误且无有效描述，加入黑名单: {article_url}")

        return ArticleContent(
            title=title or "Unknown",
            url=article_url,
            published=self._parse_timestamp(published),
            author=author or "Unknown",
            content="",
            success=False,
            extraction_method="failed"
        )

    def _clean_text(self, text: str) -> str:
        """
        清理文本：移除多余空行和空白

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 分割成行
        lines = text.split("\n")
        # 移除空行和只包含空白字符的行
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        # 用单空行连接
        return "\n".join(cleaned_lines)

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

        if non_printable / total_chars > 0.1:
            logger.warning(f"内容包含大量不可打印字符 ({non_printable}/{total_chars})")
            return False

        # 检查 null 字符
        null_count = content.count('\x00')
        if null_count > 0:
            logger.warning(f"内容包含 {null_count} 个 null 字符")
            return False

        # 验证 UTF-8 编码
        try:
            content.encode('utf-8').decode('utf-8')
        except UnicodeError:
            logger.warning("内容编码验证失败")
            return False

        return True

    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """
        解析时间戳为 ISO 8601 格式

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
        except Exception:
            logger.debug(f"解析时间戳失败: {timestamp}")
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
                "published": self._parse_timestamp(
                    article.publish_date.isoformat() if article.publish_date else None
                ),
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
