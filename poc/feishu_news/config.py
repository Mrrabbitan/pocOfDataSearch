"""配置管理模块"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_FOLDER_TOKEN = os.getenv("FEISHU_FOLDER_TOKEN", "")
FEISHU_WIKI_NODE_TOKEN = os.getenv("FEISHU_WIKI_NODE_TOKEN", "")

# 飞书 API 地址
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"
FEISHU_TOKEN_URL = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
FEISHU_CREATE_DOC_URL = f"{FEISHU_BASE_URL}/docx/v1/documents"
FEISHU_DOC_BLOCKS_URL = f"{FEISHU_BASE_URL}/docx/v1/documents/{{doc_id}}/blocks/{{block_id}}/children"
FEISHU_CREATE_FILE_URL = f"{FEISHU_BASE_URL}/drive/v1/files/create_folder"
FEISHU_PERMISSION_URL = f"{FEISHU_BASE_URL}/drive/v1/permissions/{{token}}/members"
FEISHU_WIKI_GET_NODE_URL = f"{FEISHU_BASE_URL}/wiki/v2/spaces/get_node"
FEISHU_WIKI_CREATE_NODE_URL = f"{FEISHU_BASE_URL}/wiki/v2/spaces/{{space_id}}/nodes"

# 新闻配置
NEWS_MAX_ARTICLES = int(os.getenv("NEWS_MAX_ARTICLES", "15"))
NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "zh")
NEWS_SCHEDULE_TIME = os.getenv("NEWS_SCHEDULE_TIME", "09:00")
NEWS_TODAY_ONLY = os.getenv("NEWS_TODAY_ONLY", "1") == "1"

# 飞书群聊配置（机器人发送）
FEISHU_GROUP_CHAT_ID = os.getenv("FEISHU_GROUP_CHAT_ID", "")
FEISHU_GROUP_NAME = os.getenv("FEISHU_GROUP_NAME", "")

# 企业微信群机器人配置
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")
WECOM_WEBHOOK_SECRET = os.getenv("WECOM_WEBHOOK_SECRET", "")
WECOM_MENTION_MOBILES = [
    m.strip() for m in os.getenv("WECOM_MENTION_MOBILES", "").split(",") if m.strip()
]

# AI 新闻源
NEWS_SOURCES = [
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/",
        "type": "web",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/",
        "type": "web",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence",
        "type": "web",
    },
    {
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/",
        "type": "web",
    },
    {
        "name": "AI News",
        "url": "https://artificialintelligence-news.com/",
        "type": "web",
    },
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/",
        "type": "web",
    },
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/",
        "type": "web",
    },
]

# 搜索关键词
SEARCH_QUERIES = [
    "AI news today 2026",
    "artificial intelligence breakthrough latest",
    "大模型 最新进展 2026",
    "AI 科技新闻 今日",
    "LLM new model release 2026",
    "AI startup funding news",
]
