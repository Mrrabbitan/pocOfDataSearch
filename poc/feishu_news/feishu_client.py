"""飞书 Open API 客户端 —— 认证、文档创建、内容写入、权限管理"""

import time
import logging
import json
import requests
from typing import Optional
from urllib.parse import quote

from config import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    FEISHU_BASE_URL,
    FEISHU_TOKEN_URL,
    FEISHU_CREATE_DOC_URL,
    FEISHU_FOLDER_TOKEN,
    FEISHU_WIKI_NODE_TOKEN,
    FEISHU_WIKI_GET_NODE_URL,
    FEISHU_WIKI_CREATE_NODE_URL,
)

logger = logging.getLogger(__name__)


class FeishuClient:
    """飞书 API 客户端"""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id or FEISHU_APP_ID
        self.app_secret = app_secret or FEISHU_APP_SECRET
        self._tenant_token: Optional[str] = None
        self._token_expires_at: float = 0

        if not self.app_id or not self.app_secret:
            raise ValueError(
                "飞书 App ID 和 App Secret 未配置。\n"
                "请在 .env 文件中设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET。\n"
                "获取地址: https://open.feishu.cn/app"
            )

    # ── 认证 ──────────────────────────────────────────────

    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token (自动缓存与续期)"""
        if self._tenant_token and time.time() < self._token_expires_at:
            return self._tenant_token

        resp = requests.post(
            FEISHU_TOKEN_URL,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data.get('msg')}")

        self._tenant_token = data["tenant_access_token"]
        self._token_expires_at = time.time() + data.get("expire", 7200) - 300
        logger.info("✅ 飞书认证成功")
        return self._tenant_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_tenant_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def test_connection(self) -> bool:
        """测试飞书 API 连通性"""
        try:
            self._get_tenant_token()
            return True
        except Exception as e:
            logger.error(f"❌ 飞书 API 连接失败: {e}")
            return False

    # ── 文档创建 ──────────────────────────────────────────

    def create_document(self, title: str) -> dict:
        """
        创建飞书云文档并设置公开分享
        流程: Drive API 创建 → 设置链接可编辑 → 尝试移入知识库
        返回: {"document_id": "...", "url": "..."}
        """
        # 1) 通过 Drive API 创建文档
        payload = {"title": title}
        if FEISHU_FOLDER_TOKEN:
            payload["folder_token"] = FEISHU_FOLDER_TOKEN

        resp = requests.post(
            FEISHU_CREATE_DOC_URL,
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"创建文档失败 (code={data.get('code')}): {data.get('msg')}")

        doc = data["data"]["document"]
        doc_id = doc["document_id"]
        logger.info(f"📄 文档已创建: {title} (id={doc_id})")

        # 2) 设置链接分享 (任何人可通过链接查看)
        self._set_link_sharing(doc_id)

        # 3) 尝试移入知识库 (如果配置了 wiki token)
        wiki_url = None
        if FEISHU_WIKI_NODE_TOKEN:
            wiki_url = self._try_move_to_wiki(doc_id)

        url = wiki_url or f"https://feishu.cn/docx/{doc_id}"
        logger.info(f"🔗 文档链接: {url}")

        return {"document_id": doc_id, "title": title, "url": url}

    def _set_link_sharing(self, doc_id: str):
        """设置文档链接分享为 '知道链接的人可阅读'"""
        perm_url = f"{FEISHU_BASE_URL}/drive/v1/permissions/{doc_id}/public?type=docx"
        payload = {
            "external_access_entity": "open",
            "security_entity": "anyone_can_view",
            "comment_entity": "anyone_can_view",
            "share_entity": "anyone",
            "link_share_entity": "anyone_readable",
        }
        try:
            resp = requests.patch(
                perm_url, headers=self._headers(), json=payload, timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                logger.info("🔓 链接分享已开启 (任何人可通过链接查看)")
            else:
                logger.warning(f"⚠️  设置分享失败: {data.get('msg')}")
        except Exception as e:
            logger.warning(f"⚠️  设置分享时出错: {e}")

    def _try_move_to_wiki(self, doc_id: str) -> Optional[str]:
        """尝试将文档移入知识库 (可能因权限不足而失败，不影响主流程)"""
        try:
            # 获取 wiki 信息
            url1 = f"{FEISHU_BASE_URL}/wiki/v2/spaces/get_node?token={FEISHU_WIKI_NODE_TOKEN}"
            node_resp = requests.get(url1, headers=self._headers(), timeout=10)
            node_data = node_resp.json()
            if node_data.get("code") != 0:
                return None

            node = node_data["data"]["node"]
            space_id = node["space_id"]
            parent_token = node["node_token"]

            # 移入知识库
            move_url = f"{FEISHU_BASE_URL}/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki"
            move_payload = {
                "parent_wiki_token": parent_token,
                "obj_type": "docx",
                "obj_token": doc_id,
            }
            resp = requests.post(
                move_url, headers=self._headers(), json=move_payload, timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                wiki_node = data["data"]["node"]
                wiki_url = f"https://feishu.cn/wiki/{wiki_node['node_token']}"
                logger.info(f"📚 已移入知识库: {wiki_url}")
                return wiki_url
            else:
                logger.info("ℹ️  未能移入知识库（权限不足），文档将通过链接分享访问")
                return None
        except Exception:
            return None

    # ── 文档内容写入 ─────────────────────────────────────

    def write_blocks(self, document_id: str, block_id: str, children: list, index: int = -1) -> dict:
        """向文档指定 block 追加子 block"""
        url = f"{FEISHU_BASE_URL}/docx/v1/documents/{document_id}/blocks/{block_id}/children?document_revision_id=-1"
        payload = {"children": children}
        if index >= 0:
            payload["index"] = index
        resp = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(
                f"写入文档失败 (code={data.get('code')}): {data.get('msg')}"
            )
        return data.get("data", {})

    def get_document_root_block(self, document_id: str) -> str:
        """获取文档根 block_id"""
        return document_id

    # ── 群消息发送 ───────────────────────────────────────

    def send_group_message(self, chat_id: str, text: str) -> dict:
        """发送文本消息到飞书群聊"""
        url = f"{FEISHU_BASE_URL}/im/v1/messages?receive_id_type=chat_id"
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"发送群消息失败 (code={data.get('code')}): {data.get('msg')}")
        return data

    def find_chat_id_by_name(self, name: str) -> Optional[str]:
        """通过群名称查找 chat_id（需开通 im:chat:readonly 权限）"""
        url = f"{FEISHU_BASE_URL}/im/v1/chats"
        page_token = None
        while True:
            params = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            resp = requests.get(url, headers=self._headers(), params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(
                    f"获取群列表失败 (code={data.get('code')}): {data.get('msg')}"
                )
            for item in data["data"].get("items", []):
                if item.get("name") == name:
                    return item.get("chat_id")
            if not data["data"].get("has_more"):
                break
            page_token = data["data"].get("page_token")
        return None

    # ── 富文本 Block 构建器 ────────────────────────────────

    @staticmethod
    def heading_block(text: str, level: int = 2) -> dict:
        heading_map = {
            1: "heading1", 2: "heading2", 3: "heading3",
            4: "heading4", 5: "heading5", 6: "heading6",
        }
        type_map = {
            "heading1": 3, "heading2": 4, "heading3": 5,
            "heading4": 6, "heading5": 7, "heading6": 8,
        }
        key = heading_map.get(level, "heading2")
        return {
            "block_type": type_map[key],
            key: {"elements": [{"text_run": {"content": text}}]},
        }

    @staticmethod
    def text_block(text: str, bold: bool = False) -> dict:
        element = {"text_run": {"content": text}}
        if bold:
            element["text_run"]["text_element_style"] = {"bold": True}
        return {"block_type": 2, "text": {"elements": [element]}}

    @staticmethod
    def link_block(text: str, url: str) -> dict:
        encoded_url = quote(url, safe="")
        return {
            "block_type": 2,
            "text": {
                "elements": [
                    {
                        "text_run": {
                            "content": text,
                            "text_element_style": {"link": {"url": encoded_url}},
                        }
                    }
                ]
            },
        }

    @staticmethod
    def divider_block() -> dict:
        return {"block_type": 22, "divider": {}}

    @staticmethod
    def bullet_block(text: str) -> dict:
        return {
            "block_type": 12,
            "bullet": {"elements": [{"text_run": {"content": text}}]},
        }
