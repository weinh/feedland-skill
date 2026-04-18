"""域名黑名单并发测试"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.feedland_parser.domain_blacklist import DomainBlacklist


class TestDomainBlacklistConcurrent:
    """域名黑名单并发测试类"""

    def test_concurrent_add_same_domain(self):
        """测试并发添加相同域名"""
        blacklist = DomainBlacklist()
        url = "https://example.com/article"

        # 创建多个线程同时添加同一个域名
        def add_domain():
            blacklist.add_to_blacklist(url, reason="Test")

        threads = [threading.Thread(target=add_domain) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 应该只有一个条目
        assert len(blacklist) == 1
        assert blacklist.is_blacklisted(url)

        # 检查失败次数（应该是 10，因为每次添加都会递增）
        metadata = blacklist.get_blacklist_metadata()
        domain = blacklist.get_domain_from_url(url)
        assert metadata[domain]["fail_count"] == 10

    def test_concurrent_add_different_domains(self):
        """测试并发添加不同域名"""
        blacklist = DomainBlacklist()
        urls = [
            f"https://example{i}.com/article"
            for i in range(100)
        ]

        # 创建多个线程同时添加不同域名
        def add_url(url):
            blacklist.add_to_blacklist(url, reason="Test")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_url, url) for url in urls]
            for future in as_completed(futures):
                future.result()

        # 应该有 100 个不同的域名
        assert len(blacklist) == 100

    def test_concurrent_check_and_add(self):
        """测试并发检查和添加"""
        blacklist = DomainBlacklist()
        url = "https://example.com/article"

        results = {"checks": 0, "adds": 0}

        def check_and_add():
            # 先检查
            if not blacklist.is_blacklisted(url):
                # 如果不在黑名单中，添加
                time.sleep(0.001)  # 模拟延迟
                if blacklist.add_to_blacklist(url):
                    results["adds"] += 1
            results["checks"] += 1

        threads = [threading.Thread(target=check_and_add) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 检查了 10 次，但只添加了 1 次
        assert results["checks"] == 10
        assert results["adds"] == 1
        assert len(blacklist) == 1

    def test_concurrent_read_and_write(self):
        """测试并发读写"""
        blacklist = DomainBlacklist()
        url = "https://example.com/article"

        # 先添加一个域名
        blacklist.add_to_blacklist(url)

        results = {"reads": 0, "writes": 0}

        def read_blacklist():
            for _ in range(100):
                blacklist.is_blacklisted(url)
                blacklist.get_blacklist()
                blacklist.get_blacklist_metadata()
                results["reads"] += 1

        def write_blacklist():
            for i in range(10):
                blacklist.add_to_blacklist(f"https://test{i}.com/article", reason="Test")
                results["writes"] += 1

        # 启动多个读线程和写线程
        threads = [threading.Thread(target=read_blacklist) for _ in range(5)]
        threads.extend([threading.Thread(target=write_blacklist) for _ in range(2)])

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证结果
        assert results["reads"] == 500  # 5 threads * 100 reads
        assert results["writes"] == 20  # 2 threads * 10 writes
        assert len(blacklist) == 11  # 1 initial + 10 from writes

    def test_concurrent_length_checks(self):
        """测试并发检查长度"""
        blacklist = DomainBlacklist()
        urls = [
            f"https://example{i}.com/article"
            for i in range(50)
        ]

        results = {"lengths": []}

        def add_domain(url):
            blacklist.add_to_blacklist(url)
            # 记录当前长度
            results["lengths"].append(len(blacklist))

        def check_length():
            for _ in range(100):
                results["lengths"].append(len(blacklist))

        # 启动添加线程和检查线程
        with ThreadPoolExecutor(max_workers=10) as executor:
            add_futures = [executor.submit(add_domain, url) for url in urls]
            check_futures = [executor.submit(check_length) for _ in range(10)]

            for future in as_completed(add_futures + check_futures):
                future.result()

        # 验证最终长度
        assert len(blacklist) == 50

        # 所有长度检查都应该在 0-50 之间
        assert all(0 <= length <= 50 for length in results["lengths"])
