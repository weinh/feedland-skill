#!/usr/bin/env python3
"""测试并发连接问题"""

import time
import socket
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# 禁用警告
urllib3.disable_warnings()

def test_connection_leak():
    """测试连接泄漏问题"""
    print("🧪 测试连接池问题...")
    
    # 测试不使用 Session 的情况
    start = time.time()
    
    def fetch_no_session(i):
        try:
            # 每次创建新连接
            resp = requests.get("https://httpbin.org/delay/1", timeout=5)
            return f"OK {i}: {resp.status_code}"
        except Exception as e:
            return f"ERROR {i}: {e}"
    
    print("\n1️⃣ 不使用 Session (创建新连接):")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_no_session, i) for i in range(20)]
        for f in as_completed(futures, timeout=30):
            print(f"  {f.result()}")
    
    no_session_time = time.time() - start
    print(f"⏱️  耗时: {no_session_time:.2f}s")
    
    # 测试使用 Session 的情况
    start = time.time()
    session = requests.Session()
    
    def fetch_with_session(i):
        try:
            # 复用连接
            resp = session.get("https://httpbin.org/delay/1", timeout=5)
            return f"OK {i}: {resp.status_code}"
        except Exception as e:
            return f"ERROR {i}: {e}"
    
    print("\n2️⃣ 使用 Session (连接池复用):")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_with_session, i) for i in range(20)]
        for f in as_completed(futures, timeout=30):
            print(f"  {f.result()}")
    
    session.close()  # 关闭 Session
    session_time = time.time() - start
    print(f"⏱️  耗时: {session_time:.2f}s")
    
    print(f"\n📊 性能对比: Session 快 {no_session_time / session_time:.1f}x")


def test_timeout_precision():
    """测试超时精度"""
    print("\n\n🧪 测试超时参数...")
    
    # 测试总超时
    print("\n1️⃣ timeout=3 (总超时):")
    start = time.time()
    try:
        requests.get("https://httpbin.org/delay/10", timeout=3)
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"  ⏱️  实际超时: {elapsed:.2f}s (预期: 3s)")
    
    # 测试分开的超时
    print("\n2️⃣ timeout=(1, 3) (连接超时1s, 读取超时3s):")
    start = time.time()
    try:
        requests.get("https://httpbin.org/delay/10", timeout=(1, 3))
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"  ⏱️  实际超时: {elapsed:.2f}s (预期: ~3s)")


def test_connection_timeout():
    """测试连接超时"""
    print("\n\n🧪 测试连接超时...")
    
    # 连接到不可达的地址
    print("\n1️⃣ 连接不可达地址 (timeout=3):")
    start = time.time()
    try:
        requests.get("https://10.255.255.1:12345/test", timeout=3)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
        elapsed = time.time() - start
        print(f"  ⏱️  实际超时: {elapsed:.2f}s")
        print(f"  📝 异常类型: {type(e).__name__}")
    
    # 使用分开的超时
    print("\n2️⃣ 连接不可达地址 (timeout=(1, 5)):")
    start = time.time()
    try:
        requests.get("https://10.255.255.1:12345/test", timeout=(1, 5))
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
        elapsed = time.time() - start
        print(f"  ⏱️  实际超时: {elapsed:.2f}s (连接超时应该更快)")


if __name__ == "__main__":
    print("=" * 60)
    print("并发连接问题诊断")
    print("=" * 60)
    
    # test_connection_leak()  # 跳过网络测试
    test_timeout_precision()
    test_connection_timeout()
