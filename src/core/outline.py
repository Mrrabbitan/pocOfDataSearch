from __future__ import annotations

from typing import Any, Dict, List


def build_outline(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    title = data.get("title", "")
    outline: List[Dict[str, Any]] = []

    outline.append(
        {
            "title": "技术领域",
            "bullets": [
                f"涉及技术领域：{data.get('technical_field', '')}",
                f"核心对象：{title}",
            ],
        }
    )

    outline.append(
        {
            "title": "背景技术",
            "bullets": [
                data.get("background", ""),
                f"亟需解决的问题：{data.get('problem_to_solve', '')}",
            ],
        }
    )

    components = data.get("core_components", [])
    steps = data.get("process_steps", [])
    effects = data.get("effects", [])

    outline.append(
        {
            "title": "发明内容",
            "bullets": [
                f"技术问题：{data.get('problem_to_solve', '')}",
                f"技术方案概述：{data.get('solution_overview', '')}",
                "核心结构/模块：" + "；".join(components) if components else "核心结构/模块：",
                "方法步骤：" + "；".join(steps) if steps else "方法步骤：",
                "有益效果：" + "；".join(effects) if effects else "有益效果：",
            ],
        }
    )

    drawings = data.get("drawings", [])
    outline.append(
        {
            "title": "附图说明",
            "bullets": drawings if drawings else ["本发明可选提供附图。"],
        }
    )

    outline.append(
        {
            "title": "具体实施方式",
            "bullets": [
                data.get("embodiments", ""),
                "关键参数：" + data.get("parameters", ""),
                "控制逻辑：" + data.get("control_logic", ""),
                "替换方案：" + data.get("alternatives", ""),
            ],
        }
    )

    application = data.get("application_scenarios", "")
    outline.append(
        {
            "title": "应用场景",
            "bullets": [application] if application else ["可适用于多种行业场景。"],
        }
    )

    return outline
