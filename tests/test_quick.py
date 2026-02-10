#!/usr/bin/env python3
"""快速单元测试 - 验证基本功能（无需网络请求）"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feedland_parser import Config, FeedTracker


def test_config_management():
    """测试配置管理"""
    print("=" * 60)
    print("测试 1: 配置管理")
    print("=" * 60)

    import tempfile
    import os
    import json

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "url": "https://example.com/opml",
            "threads": 5,
            "his": {}
        }
        json.dump(test_config, f)
        temp_file = f.name

    try:
        # 测试加载配置
        config = Config(temp_file)
        config.load()

        assert config.url == "https://example.com/opml"
        assert config.threads == 5
        assert config.his is not None
        print("   ✅ 配置加载测试通过")

        # 测试更新历史记录
        config.update_history("https://example.com/feed.xml", "2025-02-09T10:00:00Z")
        assert "https://example.com/feed.xml" in config.his

        print("   ✅ 历史记录更新测试通过")

        # 测试保存配置
        config.save()

        # 重新加载验证
        new_config = Config(temp_file)
        new_config.load()
        assert "https://example.com/feed.xml" in new_config.his

        print("   ✅ 配置保存测试通过")

        print("\n✅ 配置管理测试完成！\n")
        return True

    finally:
        os.unlink(temp_file)


def test_tracker():
    """测试时间戳跟踪器"""
    print("=" * 60)
    print("测试 2: 时间戳跟踪器")
    print("=" * 60)

    from feedland_parser import FeedTracker

    # 创建模拟配置
    class MockConfig:
        def __init__(self):
            self._his = {}

        @property
        def his(self):
            return self._his

        @his.setter
        def his(self, value):
            self._his = value

        def save(self):
            pass

    config = MockConfig()
    tracker = FeedTracker(config)

    # 测试加载历史记录
    tracker.load_history()
    assert len(tracker._history) == 0
    print("   ✅ 历史记录加载测试通过")

    # 测试获取时间戳
    timestamp = tracker.get_last_timestamp("https://example.com/feed.xml")
    assert timestamp is None
    print("   ✅ 获取不存在的 feed 时间戳测试通过")

    # 测试更新时间戳
    tracker.update_timestamp("https://example.com/feed.xml", "2025-02-09T10:00:00Z")
    timestamp = tracker.get_last_timestamp("https://example.com/feed.xml")
    assert timestamp == "2025-02-09T10:00:00Z"
    print("   ✅ 更新时间戳测试通过")

    # 测试保存历史记录
    tracker.save_history()
    assert "https://example.com/feed.xml" in config._his
    print("   ✅ 保存历史记录测试通过")

    print("\n✅ 时间戳跟踪器测试完成！\n")
    return True


def test_deduplicator():
    """测试去重器"""
    print("=" * 60)
    print("测试 3: 去重器")
    print("=" * 60)

    from feedland_parser import Deduplicator, FeedTracker

    class MockConfig:
        def __init__(self):
            self.history = {}

    config = MockConfig()
    tracker = FeedTracker(config)
    tracker._history = {
        "https://example.com/feed.xml": "2025-02-09T10:00:00Z"
    }

    deduplicator = Deduplicator(tracker)

    # 测试新文章
    new_article = {
        "title": "New Article",
        "url": "https://example.com/new-article",
        "published": "2025-02-09T11:00:00Z"
    }

    is_new = deduplicator.is_new_article(
        "https://example.com/feed.xml",
        new_article["url"],
        new_article["published"]
    )
    assert is_new is True
    print("   ✅ 新文章检测测试通过")

    # 测试旧文章
    old_article = {
        "title": "Old Article",
        "url": "https://example.com/old-article",
        "published": "2025-02-09T09:00:00Z"
    }

    is_new = deduplicator.is_new_article(
        "https://example.com/feed.xml",
        old_article["url"],
        old_article["published"]
    )
    assert is_new is False
    print("   ✅ 旧文章过滤测试通过")

    print("\n✅ 去重器测试完成！\n")
    return True


def run_all_tests():
    """运行所有快速测试"""
    print("\n🚀 开始运行快速测试...\n")

    tests = [
        test_config_management,
        test_tracker,
        test_deduplicator,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ {test_func.__name__} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # 汇总结果
    print("=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
