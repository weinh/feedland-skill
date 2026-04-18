"""域名黑名单模块单元测试"""

import pytest
from datetime import datetime
from src.feedland_parser.domain_blacklist import DomainBlacklist


class TestDomainBlacklist:
    """域名黑名单测试类"""

    def test_init_empty(self):
        """测试初始化空黑名单"""
        blacklist = DomainBlacklist()
        assert len(blacklist) == 0
        assert blacklist.get_blacklist() == set()

    def test_init_with_initial_blacklist(self):
        """测试使用初始黑名单初始化"""
        initial = {"example.com", "test.org"}
        blacklist = DomainBlacklist(initial_blacklist=initial)
        assert len(blacklist) == 2
        assert "example.com" in blacklist
        assert "test.org" in blacklist

    def test_get_domain_from_url(self):
        """测试从 URL 提取域名"""
        assert DomainBlacklist.get_domain_from_url("https://example.com/article") == "example.com"
        assert DomainBlacklist.get_domain_from_url("http://test.org/path/to/page") == "test.org"
        assert DomainBlacklist.get_domain_from_url("https://www.example.com/article") == "example.com"
        assert DomainBlacklist.get_domain_from_url("invalid-url") is None

    def test_is_blacklisted_with_domain(self):
        """测试检查域名是否在黑名单中（直接域名）"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")

        assert blacklist.is_blacklisted("example.com")
        assert not blacklist.is_blacklisted("test.org")

    def test_is_blacklisted_with_url(self):
        """测试检查域名是否在黑名单中（通过 URL）"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")

        assert blacklist.is_blacklisted("https://example.com/article")
        assert blacklist.is_blacklisted("http://example.com/path")
        assert not blacklist.is_blacklisted("https://test.org/article")

    def test_add_to_blacklist_with_domain(self):
        """测试添加域名到黑名单（直接域名）"""
        blacklist = DomainBlacklist()
        result = blacklist.add_to_blacklist("example.com", reason="Test")

        assert result is True
        assert "example.com" in blacklist
        assert len(blacklist) == 1

    def test_add_to_blacklist_with_url(self):
        """测试添加域名到黑名单（通过 URL）"""
        blacklist = DomainBlacklist()
        result = blacklist.add_to_blacklist("https://example.com/article", reason="Test")

        assert result is True
        assert "example.com" in blacklist
        assert len(blacklist) == 1

    def test_add_duplicate_domain(self):
        """测试添加重复域名"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")
        result = blacklist.add_to_blacklist("example.com")

        assert result is False
        assert len(blacklist) == 1

    def test_add_duplicate_url(self):
        """测试添加重复 URL（提取相同域名）"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("https://example.com/article1")
        result = blacklist.add_to_blacklist("https://example.com/article2")

        assert result is False
        assert len(blacklist) == 1

    def test_get_blacklist_metadata(self):
        """测试获取黑名单元数据"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com", reason="Test reason")

        metadata = blacklist.get_blacklist_metadata()

        assert "example.com" in metadata
        assert metadata["example.com"]["reason"] == "Test reason"
        assert metadata["example.com"]["fail_count"] == 1
        assert "added_at" in metadata["example.com"]

    def test_contains_operator(self):
        """测试 'in' 操作符"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")

        assert "example.com" in blacklist
        assert "test.org" not in blacklist
        assert "https://example.com/article" in blacklist

    def test_repr(self):
        """测试字符串表示"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")

        repr_str = repr(blacklist)

        assert "DomainBlacklist" in repr_str
        assert "count=1" in repr_str

    def test_fail_count_increment(self):
        """测试失败次数递增"""
        blacklist = DomainBlacklist()
        blacklist.add_to_blacklist("example.com")

        metadata = blacklist.get_blacklist_metadata()
        assert metadata["example.com"]["fail_count"] == 1

        # 再次添加（应该递增失败次数）
        blacklist.add_to_blacklist("example.com")

        metadata = blacklist.get_blacklist_metadata()
        assert metadata["example.com"]["fail_count"] == 2

    def test_www_prefix_removal(self):
        """测试 www. 前缀移除"""
        blacklist = DomainBlacklist()
        domain = DomainBlacklist.get_domain_from_url("https://www.example.com/article")

        assert domain == "example.com"
        assert domain != "www.example.com"

    def test_invalid_url_handling(self):
        """测试无效 URL 处理"""
        result = DomainBlacklist.get_domain_from_url("")
        assert result is None

        result = DomainBlacklist.get_domain_from_url("not-a-url")
        assert result is None

        result = DomainBlacklist.get_domain_from_url("ftp://example.com")
        # ftp URL 也应该能提取域名
        assert result == "example.com"