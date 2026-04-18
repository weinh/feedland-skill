"""RSS 链接集成测试 - 测试实际 RSS 链接"""

import feedparser
from feedland_parser.opml_parser import FeedInfo
from feedland_parser.article_extractor import ArticleExtractor


def test_caozsay_rss_link():
    """测试 caoz的梦呓 RSS 链接"""
    rss_url = "https://plink.anyfeeder.com/weixin/caozsay"
    
    print(f"\n{'='*60}")
    print(f"测试 RSS 链接: {rss_url}")
    print(f"{'='*60}")
    
    # 1. 测试 RSS 是否可访问
    print("\n1️⃣ 测试 RSS 可访问性...")
    try:
        feed = feedparser.parse(rss_url)
        assert feed is not None
        print(f"   ✅ RSS 解析成功")
    except Exception as e:
        print(f"   ❌ RSS 解析失败: {e}")
        raise
    
    # 2. 验证 Feed 信息
    print("\n2️⃣ 验证 Feed 信息...")
    assert hasattr(feed, 'feed'), "Feed 对象应该有 feed 属性"
    feed_title = feed.feed.get('title', 'Unknown')
    print(f"   📰 Feed 标题: {feed_title}")
    assert feed_title, "Feed 标题不应为空"
    
    # 3. 验证文章数量
    print("\n3️⃣ 验证文章数量...")
    assert hasattr(feed, 'entries'), "Feed 对象应该有 entries 属性"
    article_count = len(feed.entries)
    print(f"   📄 文章数量: {article_count}")
    assert article_count > 0, "应该至少有一篇文章"
    
    # 4. 验证文章内容
    print("\n4️⃣ 验证文章内容...")
    for i, entry in enumerate(feed.entries[:3]):  # 只检查前 3 篇
        print(f"\n   文章 {i+1}:")
        
        # 检查标题
        title = entry.get('title', 'Unknown')
        print(f"      标题: {title[:50]}...")
        assert title, f"文章 {i+1} 应该有标题"
        
        # 检查链接
        link = entry.get('link', '')
        print(f"      链接: {link[:60]}...")
        assert link, f"文章 {i+1} 应该有链接"
        
        # 检查发布时间
        published = entry.get('published', '')
        print(f"      发布时间: {published}")
        assert published, f"文章 {i+1} 应该有发布时间"
        
        # 检查内容（description 或 content）
        content = entry.get('description', '') or entry.get('content', '')
        if isinstance(content, list):
            content = content[0].get('value', '') if content else ''
        print(f"      内容长度: {len(content)} 字符")
        assert len(content) > 0, f"文章 {i+1} 应该有内容"
    
    # 5. 创建 FeedInfo 对象
    print("\n5️⃣ 创建 FeedInfo 对象...")
    feed_info = FeedInfo(
        url=rss_url,
        title=feed_title,
        feed_type="RSS"
    )
    print(f"   ✅ FeedInfo 创建成功: {feed_info.title}")
    
    print(f"\n{'='*60}")
    print(f"✅ RSS 链接测试通过！")
    print(f"{'='*60}\n")
    
    return True


if __name__ == "__main__":
    try:
        test_caozsay_rss_link()
        print("所有测试通过！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
