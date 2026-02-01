from __future__ import annotations

from typing import Any, Dict, List

from .schema import QUESTIONS, Question


def parse_list(value: str) -> List[str]:
    items: List[str] = []
    for raw in value.replace("；", ";").replace("，", ",").split(";"):
        for part in raw.split(","):
            item = part.strip()
            if item:
                items.append(item)
    return items


def parse_dict(value: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for raw in value.replace("；", ";").split(";"):
        item = raw.strip()
        if not item:
            continue
        if "=" not in item:
            continue
        key, desc = item.split("=", 1)
        key = key.strip()
        desc = desc.strip()
        if key and desc:
            pairs[key] = desc
    return pairs


def normalize_value(value: Any, qtype: str) -> Any:
    if qtype == "list":
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return parse_list(str(value))
    if qtype == "dict":
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k).strip(): str(v).strip() for k, v in value.items() if str(k).strip()}
        return parse_dict(str(value))
    if value is None:
        return ""
    return str(value).strip()


def normalize_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(data)
    for q in QUESTIONS:
        if q.key in normalized:
            normalized[q.key] = normalize_value(normalized[q.key], q.qtype)
    return normalized


def _prompt_text(question: Question) -> str:
    hint = f"提示：{question.help}" if question.help else ""
    suffix = "（必填）" if question.required else "（可选）"
    lines = [f"{question.label}{suffix}"]
    if hint:
        lines.append(hint)
    return "\n".join(lines) + "\n> "


def collect_inputs(
    initial_data: Dict[str, Any],
    input_func=input,
    print_func=print,
) -> Dict[str, Any]:
    data = normalize_inputs(initial_data or {})
    for question in QUESTIONS:
        existing = data.get(question.key)
        if question.qtype == "list" and isinstance(existing, list) and existing:
            continue
        if question.qtype == "dict" and isinstance(existing, dict) and existing:
            continue
        if question.qtype == "text" and isinstance(existing, str) and existing:
            continue

        while True:
            answer = input_func(_prompt_text(question)).strip()
            if not answer:
                if question.required:
                    print_func("该项必填，请补充。")
                    continue
                if question.default is not None:
                    data[question.key] = normalize_value(question.default, question.qtype)
                break

            value = normalize_value(answer, question.qtype)
            if question.required and not value:
                print_func("该项必填，请补充。")
                continue
            data[question.key] = value
            break
    return data
