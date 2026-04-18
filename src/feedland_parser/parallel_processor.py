"""并行处理模块"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Any
from .feed_parser import FeedParser, FeedResult
from .filter import Filter
from .opml_parser import FeedInfo
from threading import Lock

logger = logging.getLogger(__name__)


class ParallelFeedProcessor:
    """并行 Feed 处理器"""

    def __init__(
        self,
        feed_parser: FeedParser,
        filter: Filter,
        max_workers: int = 10
    ):
        """
        初始化并行处理器

        Args:
            feed_parser: Feed 解析器
            filter: 文章过滤器
            max_workers: 最大工作线程数
        """
        self.feed_parser = feed_parser
        self.filter = filter
        self.max_workers = max_workers
        self._lock = Lock()  # 用于线程安全地更新 filter

    def process_feeds_parallel(
        self,
        feed_infos: List[FeedInfo],
        progress_callback: Callable[[int, int, FeedResult], None] = None
    ) -> List[FeedResult]:
        """
        并行处理多个 feeds

        Args:
            feed_infos: Feed 信息列表
            progress_callback: 进度回调函数 (current, total, result)

        Returns:
            Feed 结果列表
        """
        results = []
        total = len(feed_infos)
        completed = 0

        logger.info(f"开始并行处理 {total} 个 feeds，使用 {self.max_workers} 个线程")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_feed = {
                executor.submit(self._process_single_feed, feed_info): feed_info
                for feed_info in feed_infos
            }

            # 收集结果
            for future in as_completed(future_to_feed):
                feed_info = future_to_feed[future]
                try:
                    result = future.result()
                    results.append(result)

                    completed += 1

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(completed, total, result)

                    logger.info(f"进度: {completed}/{total} - {feed_info.title}")

                except Exception as e:
                    logger.error(f"处理 feed 时发生错误 {feed_info.url}: {e}")
                    # 创建失败结果
                    results.append(FeedResult(
                        feed_info=feed_info,
                        articles=[],
                        success=False,
                        error=str(e)
                    ))
                    completed += 1

        # 按原始顺序排序结果
        feed_url_to_result = {r.feed_info.url: r for r in results}
        results = [feed_url_to_result[feed_info.url] for feed_info in feed_infos]

        # 保存历史记录
        self._save_history()

        logger.info(f"并行处理完成: {len(results)} 个 feeds")
        return results

    def _process_single_feed(self, feed_info: FeedInfo) -> FeedResult:
        """
        处理单个 feed

        Args:
            feed_info: Feed 信息

        Returns:
            Feed 结果
        """
        try:
            # 解析 feed
            result = self.feed_parser.parse_feed(feed_info)

            if result.success and result.articles:
                # 更新 filter（使用最新文章的 ID）
                with self._lock:
                    # 找到第一篇文章的 ID（最新的文章）
                    latest_id = None
                    id_type = None
                    for article in result.articles:
                        if article.get("_id"):
                            latest_id = article["_id"]
                            id_type = article.get("_id_type", "unknown")
                            break

                    if latest_id:
                        self.filter.update_id(feed_info.url, latest_id)
                        logger.debug(f"更新 feed ID: {feed_info.url} -> {latest_id[:50]}... (类型: {id_type})")

            return result

        except Exception as e:
            logger.error(f"处理单个 feed 时发生错误 {feed_info.url}: {e}")
            return FeedResult(
                feed_info=feed_info,
                articles=[],
                success=False,
                error=str(e)
            )

    def _save_history(self) -> None:
        """保存历史记录（线程安全）"""
        with self._lock:
            try:
                self.filter.save_history()
            except Exception as e:
                logger.error(f"保存历史记录失败: {e}")

    def get_successful_results(self, results: List[FeedResult]) -> List[FeedResult]:
        """
        获取成功的结果

        Args:
            results: Feed 结果列表

        Returns:
            成功的结果列表
        """
        return [r for r in results if r.success]

    def get_failed_results(self, results: List[FeedResult]) -> List[FeedResult]:
        """
        获取失败的结果

        Args:
            results: Feed 结果列表

        Returns:
            失败的结果列表
        """
        return [r for r in results if not r.success]

    def get_all_articles(self, results: List[FeedResult]) -> List[Dict]:
        """
        获取所有文章

        Args:
            results: Feed 结果列表

        Returns:
            所有文章列表
        """
        articles = []
        for result in results:
            if result.success:
                articles.extend(result.articles)
        return articles

    def get_summary(self, results: List[FeedResult]) -> Dict[str, Any]:
        """
        获取处理摘要

        Args:
            results: Feed 结果列表

        Returns:
            摘要字典
        """
        successful = self.get_successful_results(results)
        failed = self.get_failed_results(results)
        all_articles = self.get_all_articles(results)

        return {
            "total_feeds": len(results),
            "successful_feeds": len(successful),
            "failed_feeds": len(failed),
            "total_articles": len(all_articles),
            "failed_feeds_list": [r.feed_info.url for r in failed],
        }