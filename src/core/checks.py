from __future__ import annotations

from typing import Any, Dict, List

from .generator import SectionContent
from .schema import REQUIRED_KEYS


def check_required_fields(data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for key in REQUIRED_KEYS:
        value = data.get(key)
        if value is None:
            issues.append(f"缺少必填字段：{key}")
            continue
        if isinstance(value, str) and not value.strip():
            issues.append(f"缺少必填字段：{key}")
        if isinstance(value, list) and not value:
            issues.append(f"缺少必填字段：{key}")
    return issues


def _collect_text(section: SectionContent) -> List[str]:
    texts = list(section.paragraphs) + list(section.bullets)
    for sub in section.subsections:
        texts.extend(_collect_text(sub))
    return texts


def _section_text(sections: List[SectionContent], title: str) -> str:
    for section in sections:
        if section.title == title:
            return "\n".join(_collect_text(section))
    return ""


def check_terms_consistency(
    sections: List[SectionContent],
    terms: Dict[str, str],
) -> List[str]:
    issues: List[str] = []
    if not terms:
        return issues

    full_text = "\n".join(["\n".join(_collect_text(section)) for section in sections])
    for term in terms.keys():
        if term not in full_text:
            issues.append(f"术语“{term}”未在正文中出现。")
    return issues


def check_effects_coverage(
    sections: List[SectionContent],
    effects: List[str],
) -> List[str]:
    issues: List[str] = []
    if not effects:
        return issues
    invention_text = _section_text(sections, "发明内容")
    for effect in effects:
        if effect and effect not in invention_text:
            issues.append(f"有益效果“{effect}”未在发明内容中体现。")
    return issues


def run_checks(data: Dict[str, Any], sections: List[SectionContent]) -> List[str]:
    issues: List[str] = []
    issues.extend(check_required_fields(data))
    issues.extend(check_terms_consistency(sections, data.get("terms") or {}))
    effects = data.get("effects_detail") or data.get("effects") or []
    issues.extend(check_effects_coverage(sections, effects))
    return issues
