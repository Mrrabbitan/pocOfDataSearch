from __future__ import annotations

import re


def safe_filename(title: str) -> str:
    name = title.strip() if title else "交底书"
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = name.replace(" ", "_")
    return name or "交底书"
