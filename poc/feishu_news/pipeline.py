"""
AI 新闻 → 飞书云文档 完整 Pipeline

功能：
1. 爬取多个 AI 科技新闻源
2. 自动分类与去重
3. 格式化为飞书云文档并发送
4. 支持定时自动执行
"""

import logging
import sys
from datetime import datetime
from collections import defaultdict

from news_crawler import crawl_ai_news, NewsArticle
from feishu_client import FeishuClient
from config import FEISHU_GROUP_CHAT_ID, FEISHU_GROUP_NAME

logger = logging.getLogger(__name__)


def _build_feishu_blocks(articles: list[NewsArticle], date_str: str) -> list[dict]:
    """将新闻列表转换为飞书文档 block 结构"""
    blocks = []
    fc = FeishuClient.__new__(FeishuClient)  # 仅用于调用 static 方法

    # ── 文档头部 ──
    blocks.append(fc.text_block(f"📅 日期: {date_str}  |  共 {len(articles)} 篇"))
    blocks.append(fc.text_block(f"⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    blocks.append(fc.divider_block())

    # ── 按分类分组 ──
    categorized: dict[str, list[NewsArticle]] = defaultdict(list)
    for a in articles:
        categorized[a.category].append(a)

    # 分类排序权重
    category_order = [
        "🔥 重大发布",
        "🔬 研究突破",
        "💰 产业动态",
        "🛠️ 工具与应用",
        "🌍 政策与伦理",
        "📰 综合资讯",
    ]

    for cat in category_order:
        cat_articles = categorized.get(cat, [])
        if not cat_articles:
            continue

        blocks.append(fc.heading_block(f"{cat} ({len(cat_articles)}篇)", level=2))

        for idx, article in enumerate(cat_articles, 1):
            # 标题 (带链接)
            blocks.append(fc.heading_block(f"{idx}. {article.title}", level=3))

            # 来源和链接
            blocks.append(fc.link_block(f"🔗 {article.source}: {article.url}", article.url))

            # 摘要
            if article.summary:
                blocks.append(fc.text_block(f"📝 {article.summary}"))

            # 发布时间
            if article.published_at:
                blocks.append(fc.text_block(f"📅 发布: {article.published_at}"))

        blocks.append(fc.divider_block())

    # ── 文档尾部 ──
    blocks.append(fc.heading_block("🎯 今日要点", level=2))
    # 取前 3 篇作为要点
    for i, a in enumerate(articles[:3], 1):
        blocks.append(fc.bullet_block(f"{a.title} ({a.source})"))

    blocks.append(fc.divider_block())
    blocks.append(fc.text_block("—— 由 AI 新闻聚合 Pipeline 自动生成 ——"))

    return blocks


def _build_group_text(articles: list[NewsArticle], doc_url: str, date_str: str) -> str:
    """构建飞书群聊消息内容"""
    lines = [
        f"📰 AI 科技日报 {date_str}",
        f"共 {len(articles)} 篇",
        f"文档链接: {doc_url}",
        "",
        "今日精选：",
    ]
    for i, a in enumerate(articles[:5], 1):
        lines.append(f"{i}. {a.title}")
    return "\n".join(lines)


def run_pipeline(dry_run: bool = False) -> dict:
    """
    执行完整 pipeline:
    1. 爬取 AI 新闻
    2. 创建飞书文档
    3. 写入内容

    参数:
        dry_run: 如果为 True，仅爬取新闻并打印，不写入飞书

    返回:
        {"status": "ok", "doc_url": "...", "article_count": N}
    """
    date_str = datetime.now().strftime("%Y年%m月%d日")
    logger.info(f"🚀 开始执行 AI 新闻 Pipeline — {date_str}")

    # 1. 爬取新闻
    logger.info("📡 Phase 1: 爬取 AI 科技新闻...")
    articles = crawl_ai_news()

    if not articles:
        logger.warning("⚠️  未爬取到任何新闻，Pipeline 终止")
        return {"status": "empty", "article_count": 0}

    logger.info(f"✅ 共获取 {len(articles)} 篇新闻")

    # 2. Dry Run 模式
    if dry_run:
        logger.info("\n📋 [DRY RUN] 新闻预览:")
        for i, a in enumerate(articles, 1):
            logger.info(f"  [{i}] [{a.category}] {a.title}")
            logger.info(f"      来源: {a.source}")
            logger.info(f"      链接: {a.url}")
            if a.summary:
                logger.info(f"      摘要: {a.summary[:80]}...")
        return {
            "status": "dry_run",
            "article_count": len(articles),
            "articles": [{"title": a.title, "url": a.url, "category": a.category} for a in articles],
        }

    # 3. 创建飞书文档
    logger.info("📄 Phase 2: 创建飞书云文档...")
    client = FeishuClient()
    doc_title = f"📰 AI 科技日报 — {date_str}"
    doc = client.create_document(doc_title)
    doc_id = doc["document_id"]
    doc_url = doc["url"]
    logger.info(f"   文档已创建: {doc_url}")

    # 4. 写入内容
    logger.info("✍️  Phase 3: 写入新闻内容...")
    blocks = _build_feishu_blocks(articles, date_str)

    # 飞书 API 每次最多写入 50 个 block，分批处理
    BATCH_SIZE = 50
    root_block_id = client.get_document_root_block(doc_id)

    for i in range(0, len(blocks), BATCH_SIZE):
        batch = blocks[i : i + BATCH_SIZE]
        client.write_blocks(doc_id, root_block_id, batch)
        logger.info(f"   已写入 {min(i + BATCH_SIZE, len(blocks))}/{len(blocks)} blocks")

    # 5) 发送到飞书群聊
    logger.info("📨 Phase 4: 发送到飞书群聊...")
    group_result = {"status": "skipped"}
    chat_id = FEISHU_GROUP_CHAT_ID
    if not chat_id and FEISHU_GROUP_NAME:
        try:
            chat_id = client.find_chat_id_by_name(FEISHU_GROUP_NAME)
        except Exception as e:
            logger.warning(f"⚠️  获取群聊列表失败: {e}")
    if chat_id:
        group_text = _build_group_text(articles, doc_url, date_str)
        try:
            client.send_group_message(chat_id, group_text)
            group_result = {"status": "ok", "chat_id": chat_id}
            logger.info("✅ 已发送到飞书群聊")
        except Exception as e:
            group_result = {"status": "error", "error": str(e)}
            logger.warning(f"⚠️  群聊发送失败: {e}")
    else:
        logger.info("ℹ️  未配置群聊 chat_id，或无法通过群名称查找")

    logger.info(f"\n🎉 Pipeline 完成!")
    logger.info(f"   📄 文档: {doc_url}")
    logger.info(f"   📰 新闻数: {len(articles)} 篇")

    return {
        "status": "ok",
        "doc_url": doc_url,
        "document_id": doc_id,
        "article_count": len(articles),
        "group": group_result,
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    # 支持 --dry-run 参数
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("🏃 Dry Run 模式 — 仅爬取预览，不写入飞书")

    result = run_pipeline(dry_run=dry_run)
    print(f"\n{'='*50}")
    print(f"Pipeline 结果: {result}")
