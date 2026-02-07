"""企业微信群机器人发送模块"""

import base64
import hashlib
import hmac
import logging
import time
from typing import Optional
from urllib.parse import quote

import requests

from config import WECOM_WEBHOOK_URL, WECOM_WEBHOOK_SECRET, WECOM_MENTION_MOBILES

logger = logging.getLogger(__name__)


def _build_signed_url(webhook_url: str, secret: str) -> str:
    """若机器人启用加密，拼接 timestamp/sign"""
    timestamp = str(int(time.time()))
    string_to_sign = f"{timestamp}\n{secret}"
    signature = base64.b64encode(
        hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    separator = "&" if "?" in webhook_url else "?"
    return f"{webhook_url}{separator}timestamp={timestamp}&sign={quote(signature)}"


def send_wecom_message(
    text: str,
    webhook_url: Optional[str] = None,
    secret: Optional[str] = None,
    mention_mobiles: Optional[list[str]] = None,
) -> dict:
    """发送企业微信群机器人文本消息"""
    url = webhook_url or WECOM_WEBHOOK_URL
    if not url:
        logger.info("ℹ️  未配置企业微信群机器人 webhook，跳过发送")
        return {"status": "skipped", "reason": "no_webhook"}

    sign_secret = WECOM_WEBHOOK_SECRET if secret is None else secret
    if sign_secret:
        url = _build_signed_url(url, sign_secret)

    mobiles = WECOM_MENTION_MOBILES if mention_mobiles is None else mention_mobiles
    payload = {"msgtype": "text", "text": {"content": text}}
    if mobiles:
        payload["text"]["mentioned_mobile_list"] = mobiles

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode") == 0:
            logger.info("✅ 企业微信群机器人消息发送成功")
            return {"status": "ok", "response": data}
        logger.warning(f"⚠️  企业微信群机器人返回错误: {data}")
        return {"status": "error", "response": data}
    except Exception as e:
        logger.warning(f"⚠️  发送企业微信群机器人消息失败: {e}")
        return {"status": "error", "error": str(e)}
