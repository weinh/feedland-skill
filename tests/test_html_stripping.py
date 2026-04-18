"""测试 HTML 标签清理功能"""

import pytest
from src.feedland_parser.article_extractor import _strip_html_tags


class TestHTMLStripping:
    """测试 HTML 标签移除功能"""

    def test_strip_simple_tags(self):
        """测试移除简单 HTML 标签"""
        html = "<p>这是一段文本</p>"
        result = _strip_html_tags(html)
        assert result == "这是一段文本"

    def test_strip_nested_tags(self):
        """测试移除嵌套 HTML 标签"""
        html = "<div><p>嵌套文本</p></div>"
        result = _strip_html_tags(html)
        assert result == "嵌套文本"

    def test_strip_multiple_tags(self):
        """测试移除多个 HTML 标签"""
        html = "<p>第一段</p><p>第二段</p><p>第三段</p>"
        result = _strip_html_tags(html)
        # 标签移除后文本会连在一起，这是正常的
        assert "第一段" in result
        assert "第二段" in result
        assert "第三段" in result
        assert "<p>" not in result

    def test_strip_html_entities(self):
        """测试解码 HTML 实体"""
        html = "<p>文本&nbsp;&lt;&gt;&amp;&quot;</p>"
        result = _strip_html_tags(html)
        # HTML 实体被正确解码
        assert "文本" in result
        assert "<" in result
        assert ">" in result
        assert "&" in result
        assert '"' in result
        assert "&nbsp;" not in result
        assert "&lt;" not in result

    def test_strip_complex_html(self):
        """测试移除复杂 HTML"""
        html = """
        <article>
            <h1>标题</h1>
            <p>段落1</p>
            <p>段落2<strong>加粗</strong></p>
        </article>
        """
        result = _strip_html_tags(html)
        assert "标题" in result
        assert "段落1" in result
        assert "段落2" in result
        assert "加粗" in result
        assert "<" not in result
        assert ">" not in result

    def test_strip_links(self):
        """测试移除链接标签但保留文本"""
        html = '<a href="https://example.com">链接文本</a>'
        result = _strip_html_tags(html)
        assert result == "链接文本"
        assert "href" not in result

    def test_strip_images(self):
        """测试移除图片标签"""
        html = '<img src="image.jpg" alt="图片描述" />一些文本'
        result = _strip_html_tags(html)
        assert "一些文本" in result
        assert "<img" not in result

    def test_preserve_text_only(self):
        """测试纯文本不受影响"""
        text = "这是纯文本\n没有HTML标签"
        result = _strip_html_tags(text)
        assert result == text

    def test_empty_string(self):
        """测试空字符串"""
        result = _strip_html_tags("")
        assert result == ""

    def test_none_input(self):
        """测试 None 输入"""
        result = _strip_html_tags(None)
        assert result == ""

    def test_common_rss_description(self):
        """测试常见 RSS 描述格式"""
        html = '<p><strong>加粗文本</strong>和<em>斜体文本</em></p>'
        result = _strip_html_tags(html)
        assert "加粗文本" in result
        assert "斜体文本" in result
        assert "<p>" not in result
        assert "<strong>" not in result

    def test_decode_mdash(self):
        """测试解码 &mdash;"""
        html = "<p>文本&mdash;分隔</p>"
        result = _strip_html_tags(html)
        assert "文本—分隔" in result

    def test_decode_hellip(self):
        """测试解码 &hellip;"""
        html = "<p>省略号&hellip;</p>"
        result = _strip_html_tags(html)
        assert "省略号…" in result

    def test_real_world_example(self):
        """测试真实世界的 RSS 描述"""
        html = """
        <figure><img src="photo.jpg" /></figure>
        <p>这是一段关于<strong>重要事件</strong>的报道。</p>
        <p>更多详情请<a href="https://example.com">点击这里</a>。</p>
        """
        result = _strip_html_tags(html)
        assert "这是一段关于重要事件的报道" in result
        assert "更多详情请点击这里" in result
        assert "<figure>" not in result
        assert "<img" not in result
        assert "<a>" not in result
