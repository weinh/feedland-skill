"""命令行接口模块"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from .config import Config, DEFAULT_CONFIG
from .opml_parser import OPMLParser
from .article_extractor import ArticleExtractor
from .filter import Filter
from .feed_parser import FeedParser
from .parallel_processor import ParallelFeedProcessor
from .logger import setup_logger

__version__ = "1.0.2"

# 初始化日志（后面会根据配置重新设置）
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


def setup_logging(log_days: int = None, log_dir: str = None, verbose: bool = False, quiet: bool = False) -> None:
    """
    设置滚动日志
    
    Args:
        log_days: 日志保持天数，默认从配置读取
        log_dir: 日志目录，默认从配置读取
        verbose: 是否显示详细日志
        quiet: 是否只显示错误日志
    """
    import os
    if log_days is None:
        log_days = DEFAULT_CONFIG["log_days"]
    if log_dir is None:
        log_dir = os.path.expanduser(DEFAULT_CONFIG["log_dir"])
    else:
        log_dir = os.path.expanduser(log_dir)
    
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    
    # 使用滚动日志
    setup_logger("feedland", log_dir=log_dir, days=log_days, level=level)
    
    # 第三方库日志设置为 WARNING，减少噪音
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def main() -> int:
    """
    主函数

    Returns:
        退出码（0 表示成功，非 0 表示失败）
    """
    args = parse_arguments()

    try:
        # 1. 加载配置
        config = Config(args.config)
        config.load()

        # 2. 设置日志（使用配置中的 log_days 和 log_dir）
        setup_logging(log_days=config.log_days, log_dir=config.log_dir, verbose=args.verbose, quiet=args.quiet)
        
        # 获取 logger
        logger = logging.getLogger("feedland")
        
        logger.info("=" * 50)
        logger.info("FeedLand 摘要提取工具启动")
        logger.info("=" * 50)

        # 验证配置
        if not config.validate():
            logger.error("配置验证失败")
            return 1

        logger.info(f"配置加载成功: {config.url}")

        # 2. 加载历史记录
        logger.info("加载历史记录...")
        filter = Filter(config)
        filter.load_history()

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
        feed_parser = FeedParser(article_extractor, filter)

        # 6. 并行处理 feeds
        logger.info(f"开始并行处理 {len(feed_infos)} 个 feeds...")
        parallel_processor = ParallelFeedProcessor(
            feed_parser,
            filter,
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

        # 8. 保存结果到 JSON 文件
        result_file = os.path.expanduser(config.result_file)
        Path(result_file).parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 结果已保存到: {result_file}")

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