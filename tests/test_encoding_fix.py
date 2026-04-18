"""编码修复测试 - 验证 iDaily 等源的中文内容正常显示"""

import pytest
import requests
from src.feedland_parser.article_extractor import ArticleExtractor


class TestEncodingFix:
    """测试编码修复功能"""

    def test_idaily_encoding_fix(self):
        """测试 iDaily 源的中文内容编码修复"""
        # iDaily 移动端页面，已知存在 ISO-8859-1 编码声明问题
        url = "https://m.idai.ly/se/33bjzr"

        with ArticleExtractor() as extractor:
            result = extractor.extract(
                article_url=url,
                title="2026巴黎图书节 - April 18, 2026",
                published="2026-04-18T04:58:00Z"
            )

        # 验证内容成功提取
        assert result.success, "内容提取应该成功"
        assert len(result.content) > 100, "内容长度应该大于100字符"

        # 验证关键中文词汇正确显示
        assert "巴黎图书节" in result.content, "应包含'巴黎图书节'"
        assert "法国" in result.content, "应包含'法国'"
        assert "旅行" in result.content, "应包含'旅行'"

        # 验证没有乱码字符（如 Â、Ã 等编码错误的标志）
        # ISO-8859-1 错误解码 UTF-8 会导致这些字符
        assert "Â" not in result.content, "不应包含 ISO-8859-1 编码错误字符"
        assert "Ã" not in result.content, "不应包含 ISO-8859-1 编码错误字符"

        # 验证内容是有效的 UTF-8
        try:
            result.content.encode('utf-8').decode('utf-8')
        except UnicodeError:
            pytest.fail("内容应该是有效的 UTF-8 编码")

    def test_encoding_correction_mechanism(self):
        """测试编码修复机制"""
        # 使用一个已知有编码问题的 URL
        url = "https://m.idai.ly/se/868iFy"  # C/2025 R3 彗星文章

        with ArticleExtractor() as extractor:
            result = extractor.extract(
                article_url=url,
                title="「C/2025 R3」彗星接近地球 - April 18, 2026",
                published="2026-04-18T05:59:00Z"
            )

        # 验证中文内容正确
        assert result.success
        assert "彗星" in result.content or "C/2025 R3" in result.content
        assert "Â" not in result.content
        assert "Ã" not in result.content

    def test_requests_encoding_detection(self):
        """测试 requests 库的编码检测和修复逻辑"""
        url = "https://m.idai.ly/se/33bjzr"

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })

        response = session.get(url, timeout=(3, 10))

        # 验证编码检测逻辑
        if response.encoding == 'ISO-8859-1':
            # 应该使用 apparent_encoding
            assert response.apparent_encoding, "应该能检测到 apparent_encoding"
            response.encoding = response.apparent_encoding

        # 验证内容可以正确解码
        html = response.text
        assert len(html) > 0

        # 验证是有效的 UTF-8
        try:
            html.encode('utf-8').decode('utf-8')
        except UnicodeError:
            pytest.fail("HTML 内容应该是有效的 UTF-8 编码")
