#!/usr/bin/env python3
"""测试文章提取准确性"""

import sys
import json
import feedparser
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feedland_parser.article_extractor import ArticleExtractor

# 测试 RSS 源
TEST_FEEDS = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "sample_count": 3
    },
    {
        "name": "The Verge", 
        "url": "https://www.theverge.com/rss/index.xml",
        "sample_count": 3
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "sample_count": 3
    },
    {
        "name": "Dev.to",
        "url": "https://dev.to/feed",
        "sample_count": 3
    },
]

def test_feed(name: str, feed_url: str, sample_count: int = 3):
    """测试单个 feed 的文章提取"""
    print(f"\n{'='*60}")
    print(f"📰 测试: {name}")
    print(f"🔗 {feed_url}")
    print('='*60)

    # 解析 feed
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print(f"❌ 无法获取 feed 内容")
        return None

    print(f"✅ 获取 {len(feed.entries)} 篇文章，测试前 {sample_count} 篇")

    extractor = ArticleExtractor(timeout=15)
    results = []

    for i, entry in enumerate(feed.entries[:sample_count]):
        print(f"\n--- 文章 {i+1}/{sample_count} ---")

        # 获取文章信息
        article_url = entry.get('link') or entry.get('id', '')
        title = entry.get('title', 'Unknown')
        published = entry.get('published') or entry.get('updated', '')
        author = ''
        if hasattr(entry, 'author'):
            author = entry.author
        elif hasattr(entry, 'authors') and entry.authors:
            author = entry.authors[0].get('name', '')

        # 获取描述（用于回退）
        description = entry.get('summary', '') or entry.get('description', '')
        # 清理 HTML 标签
        from bs4 import BeautifulSoup
        if description:
            soup = BeautifulSoup(description, 'lxml')
            description = soup.get_text(strip=True)

        print(f"📝 标题: {title[:60]}...")
        print(f"🔗 URL: {article_url[:80]}...")

        # 提取正文
        try:
            result = extractor.extract(
                article_url=article_url,
                title=title,
                published=published,
                author=author,
                description=description
            )

            # 显示结果
            print(f"\n📊 提取结果:")
            print(f"   ✅ 成功: {result.success}")
            print(f"   🔧 方法: {result.extraction_method or 'N/A'}")
            print(f"   📝 字数: {len(result.content)} 字符")

            if result.success and result.content:
                # 显示前 200 字预览
                preview = result.content[:200].replace('\n', ' ').strip()
                print(f"   📖 预览: {preview}...")

            # 显示图片
            if result.images:
                print(f"   🖼️  图片: {len(result.images)} 张")
                for i, img_url in enumerate(result.images[:3]):  # 只显示前3张
                    print(f"      {i+1}. {img_url[:80]}...")

            results.append({
                "title": title,
                "url": article_url,
                "success": result.success,
                "method": result.extraction_method,
                "content_length": len(result.content),
                "images_count": len(result.images)
            })

        except Exception as e:
            print(f"   ❌ 提取异常: {e}")
            results.append({
                "title": title,
                "url": article_url,
                "success": False,
                "error": str(e)
            })

    return results


def main():
    """主函数"""
    print("🚀 开始测试文章提取准确性")
    print("="*60)

    all_results = []

    for test in TEST_FEEDS:
        try:
            results = test_feed(test["name"], test["url"], test["sample_count"])
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f"\n❌ Feed 测试异常: {test['name']}")
            print(f"   错误: {e}")

    # 汇总统计
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)

    total = len(all_results)
    success = sum(1 for r in all_results if r.get('success'))
    failed = total - success

    print(f"\n总测试: {total} 篇")
    print(f"✅ 成功: {success} ({success/total*100:.1f}%)")
    print(f"❌ 失败: {failed} ({failed/total*100:.1f}%)")

    # 按方法统计
    print("\n📈 提取方法分布:")
    method_stats = {}
    for r in all_results:
        method = r.get('method', 'failed')
        method_stats[method] = method_stats.get(method, 0) + 1

    for method, count in sorted(method_stats.items(), key=lambda x: -x[1]):
        print(f"   {method}: {count} 篇")

    # 平均字数
    success_results = [r for r in all_results if r.get('success')]
    if success_results:
        avg_length = sum(r.get('content_length', 0) for r in success_results) / len(success_results)
        print(f"\n📝 平均字数: {avg_length:.0f} 字符")


if __name__ == "__main__":
    main()
