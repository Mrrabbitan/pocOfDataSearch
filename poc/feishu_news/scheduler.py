"""定时调度器 —— 支持独立运行或被 OpenClaw cron 调用"""

import time
import logging
import schedule
from datetime import datetime

from config import NEWS_SCHEDULE_TIME
from pipeline import run_pipeline

logger = logging.getLogger(__name__)


def _job():
    """定时任务：执行新闻 pipeline"""
    logger.info(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 定时任务触发")
    try:
        result = run_pipeline(dry_run=False)
        if result["status"] == "ok":
            logger.info(f"✅ 成功发送至飞书: {result.get('doc_url', 'N/A')}")
        else:
            logger.warning(f"⚠️  Pipeline 返回: {result}")
    except Exception as e:
        logger.error(f"❌ Pipeline 执行失败: {e}", exc_info=True)


def start_scheduler():
    """启动定时调度器"""
    logger.info(f"📅 定时调度器启动 — 每天 {NEWS_SCHEDULE_TIME} 执行")
    schedule.every().day.at(NEWS_SCHEDULE_TIME).do(_job)

    # 也立即执行一次
    logger.info("🔄 首次运行...")
    _job()

    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    start_scheduler()
