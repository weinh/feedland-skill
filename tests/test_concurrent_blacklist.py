#!/usr/bin/env python3
"""并发黑名单测试 - 模拟实际使用场景"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from feedland_parser.domain_blacklist import DomainBlacklist
from feedland_parser.article_extractor import ArticleExtractor

# 模拟并发提取文章的场景
def test_concurrent_extraction():
    """测试并发提取时的黑名单操作"""
    blacklist = DomainBlacklist()
    extractor = ArticleExtractor(timeout=5, blacklist=blacklist)
    
    # 模拟 20 个并发任务
    test_urls = [
        "https://example1.com/article1",
        "https://example2.com/article2",
        "https://example3.com/article3",
        "https://timeout-site.com/article",  # 模拟超时
        "https://example4.com/article4",
        "https://example5.com/article5",
        "https://blocked-site.com/article",  # 模拟被黑名单
        "https://example6.com/article6",
        "https://example7.com/article7",
        "https://example8.com/article8",
    ]
    
    results = {"success": 0, "blacklisted": 0, "errors": []}
    results_lock = threading.Lock()
    
    def simulate_extract(url):
        """模拟提取过程"""
        try:
            # 1. 先检查黑名单
            if blacklist.is_blacklisted(url):
                with results_lock:
                    results["blacklisted"] += 1
                return f"SKIP: {url} (blacklisted)"
            
            # 2. 模拟网络请求（随机失败）
            if "timeout" in url:
                time.sleep(2)  # 模拟超时
                raise Exception("Timeout")
            
            if "blocked" in url:
                # 添加到黑名单
                blacklist.add_to_blacklist(url, reason="Blocked content")
                return f"BLOCKED: {url}"
            
            # 3. 模拟成功
            with results_lock:
                results["success"] += 1
            return f"OK: {url}"
            
        except Exception as e:
            # 失败时加入黑名单
            blacklist.add_to_blacklist(url, reason=str(e))
            with results_lock:
                results["errors"].append(str(e))
            return f"ERROR: {url} ({e})"
    
    print("🚀 开始并发测试...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(simulate_extract, url): url for url in test_urls}
        for future in as_completed(futures, timeout=30):
            try:
                result = future.result(timeout=5)
                print(f"  {result}")
            except Exception as e:
                print(f"  FUTURE ERROR: {e}")
    
    elapsed = time.time() - start
    print(f"\n⏱️  总耗时: {elapsed:.2f}s")
    print(f"📊 结果: {results}")
    print(f"📋 黑名单: {len(blacklist)} 个域名")
    
    return elapsed < 30  # 不应该超时


def test_lock_contention():
    """测试锁竞争场景"""
    blacklist = DomainBlacklist()
    
    # 快速连续添加大量域名
    def add_many(start_id):
        for i in range(100):
            url = f"https://test{start_id + i}.com/article"
            blacklist.add_to_blacklist(url, reason=f"Test {start_id + i}")
    
    def check_many():
        for i in range(100):
            blacklist.is_blacklisted(f"https://test{i}.com/article")
    
    print("\n🧪 测试锁竞争...")
    start = time.time()
    
    threads = []
    for i in range(5):
        threads.append(threading.Thread(target=add_many, args=(i * 100,)))
    for i in range(3):
        threads.append(threading.Thread(target=check_many))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    print(f"⏱️  完成 {len(blacklist)} 个域名，耗时 {elapsed:.2f}s")
    
    return len(blacklist) == 500  # 5 个线程 * 100 个域名


def test_nested_lock_calls():
    """测试潜在的锁嵌套问题"""
    blacklist = DomainBlacklist()
    
    # 先添加一个域名
    blacklist.add_to_blacklist("https://test.com/article")
    
    results = []
    
    def check_and_remove():
        if blacklist.is_blacklisted("https://test.com/article"):
            # 检查后立即删除
            result = blacklist.remove_from_blacklist("https://test.com/article")
            results.append(("remove", result))
    
    def add_and_check():
        blacklist.add_to_blacklist("https://test2.com/article")
        results.append(("add", blacklist.is_blacklisted("https://test2.com/article")))
    
    print("\n🧪 测试锁嵌套...")
    threads = [
        threading.Thread(target=check_and_remove),
        threading.Thread(target=add_and_check),
        threading.Thread(target=check_and_remove),  # 重复删除
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
        if t.is_alive():
            print("❌ 线程卡住了！")
            return False
    
    print(f"✅ 操作完成: {results}")
    return True


def test_deadlock_scenario():
    """模拟实际死锁场景"""
    blacklist = DomainBlacklist()
    
    # 模拟两个线程同时操作对方的域名
    def thread_a():
        for i in range(10):
            blacklist.add_to_blacklist(f"https://domain-a-{i}.com/article")
            time.sleep(0.001)  # 小延迟
            blacklist.is_blacklisted(f"https://domain-b-{i}.com/article")
    
    def thread_b():
        for i in range(10):
            blacklist.is_blacklisted(f"https://domain-a-{i}.com/article")
            time.sleep(0.001)
            blacklist.add_to_blacklist(f"https://domain-b-{i}.com/article")
    
    print("\n🧪 模拟死锁场景...")
    start = time.time()
    
    t1 = threading.Thread(target=thread_a)
    t2 = threading.Thread(target=thread_b)
    
    t1.start()
    t2.start()
    
    t1.join(timeout=10)
    t2.join(timeout=10)
    
    elapsed = time.time() - start
    
    if t1.is_alive() or t2.is_alive():
        print("❌ 可能存在死锁！")
        return False
    
    print(f"✅ 完成，耗时 {elapsed:.2f}s，黑名单 {len(blacklist)} 个域名")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("并发黑名单安全测试")
    print("=" * 60)
    
    tests = [
        ("并发提取测试", test_concurrent_extraction),
        ("锁竞争测试", test_lock_contention),
        ("嵌套锁测试", test_nested_lock_calls),
        ("死锁场景测试", test_deadlock_scenario),
    ]
    
    results = []
    for name, test in tests:
        print(f"\n{'=' * 60}")
        try:
            passed = test()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
