"""命令行接口模块"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, List

from .config import Config
from .opml_parser import OPMLParser
from .article_extractor import ArticleExtractor
from .tracker import FeedTracker
from .deduplicator import Deduplicator
from .feed_parser import FeedParser
from .parallel_processor import ParallelFeedProcessor

__version__ = "1.0.0"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="从 Feedland OPML 解析和提取 RSS/Atom feeds 文章内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --config ./config.json
  %(prog)s
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径（可选）"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细日志"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="只显示错误日志"
    )

    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool) -> None:
    """
    设置日志级别

    Args:
        verbose: 是否显示详细日志
        quiet: 是否只显示错误日志
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)


def main() -> int:
    """
    主函数

    Returns:
        退出码（0 表示成功，非 0 表示失败）
    """
    args = parse_arguments()
    setup_logging(args.verbose, args.quiet)

    try:
        # 1. 加载配置
        logger.info("加载配置...")
        config = Config(args.config)
        config.load()

        # 验证配置
        if not config.validate():
            logger.error("配置验证失败")
            return 1

        logger.info(f"配置加载成功: {config.url}")

        # 2. 加载历史记录
        logger.info("加载历史记录...")
        tracker = FeedTracker(config)
        tracker.load_history()

        # 3. 创建黑名单（每次启动都是空的）
        from .domain_blacklist import DomainBlacklist
        logger.info("初始化域名黑名单...")
        blacklist = DomainBlacklist()

        # 4. 解析 OPML
        logger.info("解析 OPML...")
        opml_parser = OPMLParser()
        feed_infos = opml_parser.parse_opml(config.url)

        if not feed_infos:
            logger.warning("未找到任何 feeds")
            return 0

        logger.info(f"找到 {len(feed_infos)} 个 feeds")

        # 5. 初始化处理器
        article_extractor = ArticleExtractor(blacklist=blacklist)
        deduplicator = Deduplicator(tracker)
        feed_parser = FeedParser(article_extractor, deduplicator)

        # 6. 并行处理 feeds
        logger.info(f"开始并行处理 {len(feed_infos)} 个 feeds...")
        parallel_processor = ParallelFeedProcessor(
            feed_parser,
            tracker,
            max_workers=config.threads
        )

        results = []
        total_articles = []

        def progress_callback(current: int, total: int, result) -> None:
            """进度回调"""
            logger.info(f"进度: {current}/{total} - {result.feed_info.title}")
            if result.success:
                total_articles.extend(result.articles)

        results = parallel_processor.process_feeds_parallel(
            feed_infos,
            progress_callback=progress_callback
        )

        # 7. 生成输出
        logger.info("生成输出...")
        output = generate_output(results)

        # 8. 输出 JSON
        print(json.dumps(output, indent=2, ensure_ascii=False))

        # 9. 显示摘要
        summary = parallel_processor.get_summary(results)
        logger.info(f"处理完成: {summary['successful_feeds']}/{summary['total_feeds']} 个 feeds 成功")
        logger.info(f"共提取 {summary['total_articles']} 篇文章")

        # 10. 显示黑名单统计
        if len(blacklist) > 0:
            logger.info(f"本次运行中有 {len(blacklist)} 个域名被加入黑名单")
            blacklist_metadata = blacklist.get_blacklist_metadata()
            logger.info(f"黑名单元数据: {len(blacklist_metadata)} 个条目")

        if summary["failed_feeds"] > 0:
            logger.warning(f"失败的 feeds: {', '.join(summary['failed_feeds_list'])}")

        return 0

    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
        return 1


def generate_output(results: List) -> Dict[str, Any]:
    """
    生成输出

    Args:
        results: Feed 结果列表

    Returns:
        输出字典
    """
    output = []

    for result in results:
        if result.success and result.articles:
            feed_data = {
                "feed_url": result.feed_info.url,
                "feed_title": result.feed_info.title,
                "feed_type": result.feed_info.feed_type,
                "articles": result.articles,
            }
            output.append(feed_data)

    return output


if __name__ == "__main__":
    sys.exit(main())