"""AI 科技新闻爬取模块 —— 从多个来源聚合最新 AI 新闻"""

import re
import logging
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import NEWS_SOURCES, SEARCH_QUERIES, NEWS_MAX_ARTICLES, NEWS_TODAY_ONLY

logger = logging.getLogger(__name__)

# 请求超时与 UA
TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass
class NewsArticle:
    """新闻文章数据结构"""
    title: str
    url: str
    summary: str = ""
    source: str = ""
    category: str = ""
    published_at: Optional[str] = None
    tags: list = field(default_factory=list)

    @property
    def uid(self) -> str:
        """基于 URL 的去重 ID"""
        return hashlib.md5(self.url.encode()).hexdigest()[:12]


# ── 网页爬取 ──────────────────────────────────────────────


def _fetch_page(url: str) -> Optional[BeautifulSoup]:
    """获取并解析网页"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.warning(f"⚠️  抓取失败 [{url}]: {e}")
        return None


def _extract_text(element, max_len: int = 300) -> str:
    """从 HTML 元素提取纯文本"""
    if element is None:
        return ""
    text = element.get_text(strip=True)
    return text[:max_len] + "..." if len(text) > max_len else text


def _parse_datetime(text: str) -> Optional[datetime]:
    """解析常见日期格式为 datetime"""
    if not text:
        return None
    raw = text.strip()
    if not raw:
        return None

    # ISO 8601
    candidate = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        pass

    # 2026-02-07 / 2026/02/07 / 2026.02.07
    m = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", raw)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 2026年02月07日
    m = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", raw)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return None


def _extract_published_from_soup(soup: BeautifulSoup) -> str:
    """从文章页提取发布时间"""
    meta_keys = [
        "article:published_time",
        "og:published_time",
        "publish_date",
        "pubdate",
        "date",
        "datePublished",
        "article:modified_time",
    ]
    for meta in soup.find_all("meta"):
        key = meta.get("property") or meta.get("name")
        if key in meta_keys:
            content = meta.get("content", "").strip()
            if content:
                return content

    time_el = soup.find("time")
    if time_el:
        value = time_el.get("datetime") or time_el.get("content") or time_el.get_text(strip=True)
        if value:
            return value

    return ""


def _enrich_published_at(article: NewsArticle) -> Optional[datetime]:
    """尝试补全文章发布时间"""
    dt = _parse_datetime(article.published_at or "")
    if not dt:
        soup = _fetch_page(article.url)
        if soup:
            raw = _extract_published_from_soup(soup)
            dt = _parse_datetime(raw)
    if dt:
        article.published_at = dt.isoformat()
    return dt


def _is_today(dt: datetime) -> bool:
    """判断是否为当天内容（本地时区）"""
    if dt.tzinfo:
        dt = dt.astimezone()
    return dt.date() == datetime.now().date()


def _filter_today_articles(articles: list[NewsArticle]) -> list[NewsArticle]:
    """仅保留当天新闻"""
    kept = []
    for article in articles:
        dt = _enrich_published_at(article)
        if not dt:
            continue
        if _is_today(dt):
            kept.append(article)
    logger.info(f"🧹 仅保留当天新闻: {len(kept)}/{len(articles)}")
    return kept


# ── 通用新闻提取器 ─────────────────────────────────────────


def _extract_articles_generic(soup: BeautifulSoup, base_url: str, source_name: str) -> list[NewsArticle]:
    """通用文章提取：从页面中找 <article> 或含链接的标题"""
    articles = []
    seen_urls = set()

    # 策略 1: 查找 <article> 标签
    for article_el in soup.find_all("article", limit=20):
        link = article_el.find("a", href=True)
        if not link:
            continue
        href = urljoin(base_url, link["href"])
        if href in seen_urls or not _is_valid_article_url(href, base_url):
            continue
        seen_urls.add(href)

        title_el = article_el.find(["h1", "h2", "h3", "h4"])
        title = _extract_text(title_el) or _extract_text(link)
        if not title or len(title) < 5:
            continue

        summary_el = article_el.find("p")
        summary = _extract_text(summary_el, 200)

        time_el = article_el.find("time")
        pub_time = time_el.get("datetime", "") if time_el else ""

        articles.append(
            NewsArticle(
                title=title,
                url=href,
                summary=summary,
                source=source_name,
                published_at=pub_time,
            )
        )

    # 策略 2: h2/h3 标题内链接 (补充)
    if len(articles) < 3:
        for heading in soup.find_all(["h2", "h3"], limit=30):
            link = heading.find("a", href=True)
            if not link:
                continue
            href = urljoin(base_url, link["href"])
            if href in seen_urls or not _is_valid_article_url(href, base_url):
                continue
            seen_urls.add(href)

            title = _extract_text(heading)
            if not title or len(title) < 5:
                continue

            # 尝试找相邻 <p> 作为摘要
            next_p = heading.find_next_sibling("p")
            summary = _extract_text(next_p, 200) if next_p else ""

            articles.append(
                NewsArticle(title=title, url=href, summary=summary, source=source_name)
            )

    return articles


def _is_valid_article_url(url: str, base_url: str) -> bool:
    """过滤掉非文章链接"""
    parsed = urlparse(url)
    path = parsed.path.lower()
    # 排除首页、分类页、标签页等
    skip_patterns = [
        "/category/", "/tag/", "/page/", "/author/",
        "/search", "/login", "/signup", "/about",
        "/contact", "/privacy", "/terms",
    ]
    if any(p in path for p in skip_patterns):
        return False
    # 至少要有一级以上的路径
    if path.count("/") < 2 and not path.endswith("/"):
        return True
    return len(path) > 5


# ── 中文新闻源专用提取 ────────────────────────────────────


def _extract_jiqizhixin(soup: BeautifulSoup) -> list[NewsArticle]:
    """机器之心专用提取"""
    articles = []
    for item in soup.select(".article-item, .article_item, .list-item", limit=15):
        link = item.find("a", href=True)
        if not link:
            continue
        href = urljoin("https://www.jiqizhixin.com", link["href"])
        title = _extract_text(item.find(["h2", "h3", "h4", ".title"]))
        if not title:
            title = _extract_text(link)
        summary = _extract_text(item.find(["p", ".summary", ".desc"]), 200)
        if title and len(title) > 4:
            articles.append(
                NewsArticle(title=title, url=href, summary=summary, source="机器之心")
            )
    return articles


def _extract_qbitai(soup: BeautifulSoup) -> list[NewsArticle]:
    """量子位专用提取"""
    articles = []
    for item in soup.select("article, .post-item, .news-item", limit=15):
        link = item.find("a", href=True)
        if not link:
            continue
        href = urljoin("https://www.qbitai.com", link["href"])
        title = _extract_text(item.find(["h2", "h3", "h4"]))
        if not title:
            title = _extract_text(link)
        summary = _extract_text(item.find("p"), 200)
        if title and len(title) > 4:
            articles.append(
                NewsArticle(title=title, url=href, summary=summary, source="量子位")
            )
    return articles


# ── 搜索引擎补充 ──────────────────────────────────────────


def _search_web_news(query: str) -> list[NewsArticle]:
    """通过 DuckDuckGo HTML 搜索补充新闻"""
    articles = []
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.select(".result, .web-result", limit=10):
            link = result.find("a", class_="result__a", href=True)
            if not link:
                link = result.find("a", href=True)
            if not link:
                continue

            href = link.get("href", "")
            # DuckDuckGo 有时会包装 URL
            if "uddg=" in href:
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    href = requests.utils.unquote(match.group(1))

            title = _extract_text(link)
            snippet_el = result.find(class_="result__snippet")
            summary = _extract_text(snippet_el, 200) if snippet_el else ""

            if title and href.startswith("http"):
                articles.append(
                    NewsArticle(
                        title=title, url=href, summary=summary, source="Web Search"
                    )
                )
    except Exception as e:
        logger.warning(f"⚠️  搜索失败 [{query}]: {e}")
    return articles


# ── 分类器 ────────────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "🔥 重大发布": [
        "launch", "release", "announce", "发布", "推出", "上线",
        "GPT", "Claude", "Gemini", "Llama", "DeepSeek",
    ],
    "🔬 研究突破": [
        "research", "paper", "study", "breakthrough", "论文",
        "研究", "突破", "benchmark", "SOTA",
    ],
    "💰 产业动态": [
        "funding", "acquisition", "invest", "IPO", "融资",
        "收购", "市场", "估值", "partnership", "合作",
    ],
    "🛠️ 工具与应用": [
        "tool", "framework", "open source", "API", "SDK",
        "开源", "工具", "应用", "plugin", "agent",
    ],
    "🌍 政策与伦理": [
        "regulation", "policy", "safety", "ethic", "监管",
        "政策", "安全", "伦理", "法规",
    ],
}


def _categorize(article: NewsArticle) -> str:
    """根据标题和摘要自动分类"""
    text = f"{article.title} {article.summary}".lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "📰 综合资讯"


# ── 去重 ──────────────────────────────────────────────────


def _deduplicate(articles: list[NewsArticle]) -> list[NewsArticle]:
    """基于 URL hash 和标题相似度去重"""
    seen_uids = set()
    seen_titles = set()
    unique = []
    for a in articles:
        if a.uid in seen_uids:
            continue
        # 简单标题去重：前 20 字符相同则视为重复
        title_key = a.title[:20].lower().strip()
        if title_key in seen_titles:
            continue
        seen_uids.add(a.uid)
        seen_titles.add(title_key)
        unique.append(a)
    return unique


# ── 主入口 ────────────────────────────────────────────────


def crawl_ai_news(max_articles: int = 0) -> list[NewsArticle]:
    """
    从多个来源爬取 AI 科技新闻
    返回去重、分类后的文章列表
    """
    max_articles = max_articles or NEWS_MAX_ARTICLES
    all_articles: list[NewsArticle] = []

    # 1) 爬取各新闻源
    for source in NEWS_SOURCES:
        logger.info(f"🔍 正在抓取: {source['name']} ({source['url']})")
        soup = _fetch_page(source["url"])
        if not soup:
            continue

        if "jiqizhixin" in source["url"]:
            articles = _extract_jiqizhixin(soup)
        elif "qbitai" in source["url"]:
            articles = _extract_qbitai(soup)
        else:
            articles = _extract_articles_generic(soup, source["url"], source["name"])

        logger.info(f"   → 获取到 {len(articles)} 篇文章")
        all_articles.extend(articles)

    # 2) 搜索引擎补充
    for query in SEARCH_QUERIES[:3]:  # 限制搜索次数
        logger.info(f"🔎 搜索补充: {query}")
        search_results = _search_web_news(query)
        all_articles.extend(search_results)

    # 3) 去重
    unique_articles = _deduplicate(all_articles)

    # 4) 仅保留当天
    if NEWS_TODAY_ONLY:
        unique_articles = _filter_today_articles(unique_articles)

    # 5) 分类
    for article in unique_articles:
        article.category = _categorize(article)

    # 6) 截断
    result = unique_articles[:max_articles]
    logger.info(f"✅ 共获取 {len(result)} 篇去重后的 AI 新闻")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    news = crawl_ai_news()
    for i, a in enumerate(news, 1):
        print(f"\n[{i}] [{a.category}] {a.title}")
        print(f"    来源: {a.source} | {a.url}")
        if a.summary:
            print(f"    摘要: {a.summary[:80]}...")
