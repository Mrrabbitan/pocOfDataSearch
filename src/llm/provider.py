from __future__ import annotations

import os
from typing import Any, Dict, Optional


class BaseProvider:
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> str:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> str:
        import requests

        if not model:
            raise ValueError("OpenAI provider 需要指定 model。")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def load_provider(config: Dict[str, Any]) -> Optional[BaseProvider]:
    provider = str(config.get("provider", "template")).lower()
    if provider in {"template", "local", "mock", "none"}:
        return None
    if provider == "openai":
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未找到 OpenAI API Key，可在配置中提供或设置 OPENAI_API_KEY。")
        base_url = config.get("base_url", "https://api.openai.com")
        return OpenAIProvider(api_key=api_key, base_url=base_url)
    raise ValueError(f"未知的 provider: {provider}")
