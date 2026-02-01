from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SectionContent:
    title: str
    paragraphs: List[str] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)
    subsections: List["SectionContent"] = field(default_factory=list)


def build_term_glossary(data: Dict[str, Any]) -> Dict[str, str]:
    terms: Dict[str, str] = {}
    custom_terms = data.get("terms") or {}
    if isinstance(custom_terms, dict):
        terms.update(custom_terms)

    components = data.get("core_components") or []
    for comp in components:
        comp = str(comp).strip()
        if comp and comp not in terms:
            terms[comp] = "指代本发明中的关键组成部分。"
    return terms


def _ensure_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text[-1] not in "。！？":
        return text + "。"
    return text


def _join_list(items: List[str]) -> str:
    return "、".join([item for item in items if item])


def _parse_list_value(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        normalized = value.replace("\n", ";").replace("；", ";").replace("，", ",")
        items: List[str] = []
        for raw in normalized.split(";"):
            for part in raw.split(","):
                item = part.strip()
                if item:
                    items.append(item)
        return items
    return [str(value).strip()] if str(value).strip() else []


def _normalize_steps(steps: List[str]) -> List[str]:
    normalized: List[str] = []
    for idx, step in enumerate(steps):
        text = str(step).strip()
        if not text:
            continue
        if text[:1].isdigit() or text.startswith(("S", "s")):
            normalized.append(text)
        else:
            normalized.append(f"S{idx + 1}：{text}")
    return normalized


def _has_content(section: "SectionContent") -> bool:
    if section.paragraphs or section.bullets:
        return True
    return any(_has_content(sub) for sub in section.subsections)


def _filter_sections(sections: List["SectionContent"]) -> List["SectionContent"]:
    return [section for section in sections if _has_content(section)]


def _split_paragraphs(text: str) -> Tuple[List[str], List[str]]:
    paragraphs: List[str] = []
    bullets: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        else:
            paragraphs.append(stripped)
    return paragraphs, bullets


def _load_prompt(prompt_dir: Path, name: str) -> Optional[str]:
    path = prompt_dir / f"{name}.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _render_prompt(template: str, context: Dict[str, Any]) -> str:
    text = template
    for key, value in context.items():
        token = "{{" + key + "}}"
        text = text.replace(token, str(value))
    return text


def _technical_field_section(data: Dict[str, Any]) -> SectionContent:
    title = data.get("title", "")
    field = data.get("technical_field", "")
    detail = data.get("technical_field_detail", "")
    paragraphs: List[str] = []
    if detail:
        paragraphs.append(detail.strip())
    elif field and (len(field) > 30 or "。" in field or "，" in field):
        paragraphs.append(field.strip())
    elif field:
        paragraphs.append(_ensure_sentence(f"本发明涉及{field}领域，尤其涉及{title}"))
    else:
        paragraphs.append("本发明涉及智能预测与自动化控制相关领域。")
    return SectionContent(title="技术领域", paragraphs=[p for p in paragraphs if p])


def _background_section(data: Dict[str, Any]) -> SectionContent:
    background = data.get("background", "")
    status = data.get("background_status") or background
    issues = _parse_list_value(data.get("background_issues"))
    problem = data.get("problem_to_solve", "")

    subsections: List[SectionContent] = []
    if status:
        subsections.append(
            SectionContent(title="现有技术现状", paragraphs=[_ensure_sentence(status)])
        )
    if issues:
        subsections.append(
            SectionContent(title="现有技术存在的技术问题", bullets=issues)
        )
    if problem:
        subsections.append(
            SectionContent(title="发明要解决的技术问题", paragraphs=[_ensure_sentence(problem)])
        )

    subsections = _filter_sections(subsections)
    if subsections:
        return SectionContent(title="背景技术", subsections=subsections)
    return SectionContent(title="背景技术", paragraphs=[_ensure_sentence(background)])


def _invention_content_section(data: Dict[str, Any]) -> SectionContent:
    problem = data.get("problem_to_solve", "")
    solution = data.get("solution_overview", "")
    purpose = data.get("invention_purpose", "")
    terms = build_term_glossary(data)

    if not purpose:
        if problem and solution:
            purpose = f"本发明的核心目的在于{problem}，并通过{solution}实现上述目的"
        elif problem:
            purpose = f"本发明的核心目的在于{problem}"
        elif solution:
            purpose = f"本发明提供如下技术方案：{solution}"

    subsections: List[SectionContent] = []
    if purpose:
        subsections.append(
            SectionContent(title="发明目的", paragraphs=[_ensure_sentence(purpose)])
        )

    if terms:
        term_bullets = [f"{key}：{value}" for key, value in terms.items()]
        subsections.append(
            SectionContent(title="术语约定", bullets=term_bullets)
        )

    components = _parse_list_value(data.get("core_components"))
    components_detail = _parse_list_value(data.get("core_components_detail"))
    steps_detail = _parse_list_value(data.get("process_steps_detail"))
    steps = _parse_list_value(data.get("process_steps"))
    alternatives_detail = _parse_list_value(data.get("alternatives_detail"))
    detail_present = bool(components_detail or steps_detail or alternatives_detail)

    core_paragraphs: List[str] = []
    if solution:
        core_paragraphs.append(_ensure_sentence(f"本发明通过以下技术方案实现：{solution}"))
    if data.get("control_logic") and not detail_present:
        core_paragraphs.append(
            _ensure_sentence(f"控制逻辑：{data.get('control_logic')}")
        )
    if data.get("parameters") and not detail_present:
        core_paragraphs.append(
            _ensure_sentence(f"关键参数：{data.get('parameters')}")
        )

    core_subsections: List[SectionContent] = []
    if components_detail:
        core_subsections.append(
            SectionContent(title="核心结构/模块组成", bullets=components_detail)
        )
    elif components:
        core_subsections.append(
            SectionContent(
                title="核心结构/模块组成",
                paragraphs=[
                    _ensure_sentence(f"本发明的核心结构/模块包括：{_join_list(components)}")
                ],
                bullets=components,
            )
        )

    steps_to_use = _normalize_steps(steps_detail or steps)
    if steps_to_use:
        core_subsections.append(
            SectionContent(title="预测流程步骤", bullets=steps_to_use)
        )

    alternatives = data.get("alternatives", "")
    if alternatives_detail:
        core_subsections.append(
            SectionContent(title="替换方案", bullets=alternatives_detail)
        )
    elif alternatives:
        core_subsections.append(
            SectionContent(title="替换方案", paragraphs=[_ensure_sentence(alternatives)])
        )

    core_subsections = _filter_sections(core_subsections)
    if core_paragraphs or core_subsections:
        subsections.append(
            SectionContent(
                title="核心技术方案",
                paragraphs=core_paragraphs,
                subsections=core_subsections,
            )
        )

    effects_detail = _parse_list_value(data.get("effects_detail"))
    effects = _parse_list_value(data.get("effects"))
    effects_to_use = effects_detail or effects
    if effects_to_use:
        subsections.append(
            SectionContent(title="有益效果", bullets=effects_to_use)
        )

    subsections = _filter_sections(subsections)
    if subsections:
        return SectionContent(title="发明内容", subsections=subsections)

    paragraphs = [
        _ensure_sentence(f"本发明的目的在于{problem}"),
        _ensure_sentence(f"为实现上述目的，本发明提出如下技术方案：{solution}"),
    ]
    return SectionContent(title="发明内容", paragraphs=[p for p in paragraphs if p])


def _drawings_section(data: Dict[str, Any]) -> SectionContent:
    drawings = _parse_list_value(data.get("drawings"))
    notes = data.get("drawings_notes", "")
    bullets = drawings if drawings else ["本发明可选提供附图。"]
    paragraphs = [notes] if notes else []
    return SectionContent(title="附图说明", paragraphs=paragraphs, bullets=bullets)


def _embodiments_section(data: Dict[str, Any]) -> SectionContent:
    intro = data.get("embodiments", "")
    paragraphs = [
        "以下结合具体实施例对本发明的技术方案进行说明，但不构成对本发明的限制。",
    ]
    if intro:
        paragraphs.append(_ensure_sentence(intro))

    subsections: List[SectionContent] = []
    preconditions = data.get("implementation_preconditions", "")
    if preconditions:
        subsections.append(
            SectionContent(title="实施前提", paragraphs=[_ensure_sentence(preconditions)])
        )

    steps_detail = _parse_list_value(data.get("implementation_steps_detail"))
    if not steps_detail:
        steps_detail = _parse_list_value(data.get("process_steps_detail"))
    if not steps_detail:
        steps_detail = _parse_list_value(data.get("process_steps"))
    steps_detail = _normalize_steps(steps_detail)
    if steps_detail:
        subsections.append(
            SectionContent(title="具体实施步骤", bullets=steps_detail)
        )

    implementation_effects = data.get("implementation_effects", "")
    if implementation_effects:
        subsections.append(
            SectionContent(
                title="实施效果", paragraphs=[_ensure_sentence(implementation_effects)]
            )
        )

    alternative_example = data.get("alternative_example", "")
    if alternative_example:
        subsections.append(
            SectionContent(
                title="替换方案实施示例",
                paragraphs=[_ensure_sentence(alternative_example)],
            )
        )

    subsections = _filter_sections(subsections)
    return SectionContent(
        title="具体实施方式", paragraphs=paragraphs, subsections=subsections
    )


def _application_section(data: Dict[str, Any]) -> SectionContent:
    scenarios = _parse_list_value(data.get("application_scenarios_list"))
    if not scenarios:
        scenarios = _parse_list_value(data.get("application_scenarios"))
    notes = data.get("application_notes", "")
    paragraphs: List[str] = []
    if notes:
        paragraphs.append(_ensure_sentence(notes))
    elif data.get("application_scenarios") and not scenarios:
        paragraphs.append(
            _ensure_sentence(f"本发明可广泛应用于{data.get('application_scenarios')}")
        )
    if not paragraphs and not scenarios:
        paragraphs.append("本发明可广泛应用于多种场景。")
    return SectionContent(title="应用场景", paragraphs=paragraphs, bullets=scenarios)


def build_rich_sections(data: Dict[str, Any]) -> List[SectionContent]:
    sections = [
        _technical_field_section(data),
        _background_section(data),
        _invention_content_section(data),
        _drawings_section(data),
        _embodiments_section(data),
        _application_section(data),
    ]
    return _filter_sections(sections)


def _enhance_sections_with_llm(
    sections: List[SectionContent],
    data: Dict[str, Any],
    provider: Any,
    prompt_dir: Path,
    provider_config: Dict[str, Any],
) -> List[SectionContent]:
    prompt_map = {
        "技术领域": "technical_field",
        "背景技术": "background",
        "发明内容": "invention_content",
        "附图说明": "drawings",
        "具体实施方式": "embodiments",
        "应用场景": "application",
    }
    for section in sections:
        prompt_name = prompt_map.get(section.title)
        if not prompt_name:
            continue
        template = _load_prompt(prompt_dir, prompt_name)
        if not template:
            continue
        prompt = _render_prompt(template, data)
        text = provider.generate(
            prompt,
            model=provider_config.get("model"),
            temperature=provider_config.get("temperature", 0.2),
            max_tokens=provider_config.get("max_tokens", 1200),
        )
        paragraphs, bullets = _split_paragraphs(text)
        if paragraphs:
            section.paragraphs = paragraphs + section.paragraphs
        if bullets:
            section.bullets = bullets + section.bullets
    return sections


def _local_generate_technical_field(data: Dict[str, Any]) -> SectionContent:
    title = data.get("title", "")
    field = data.get("technical_field", "")
    paragraphs = [
        _ensure_sentence(f"本发明涉及{field}领域，尤其涉及{title}")
    ]
    return SectionContent(title="技术领域", paragraphs=paragraphs)


def _local_generate_background(data: Dict[str, Any]) -> SectionContent:
    background = data.get("background", "")
    problem = data.get("problem_to_solve", "")
    paragraphs = [
        _ensure_sentence(background),
        _ensure_sentence(f"现有技术至少存在以下问题：{problem}"),
    ]
    return SectionContent(title="背景技术", paragraphs=[p for p in paragraphs if p])


def _local_generate_invention_content(data: Dict[str, Any]) -> SectionContent:
    problem = data.get("problem_to_solve", "")
    solution = data.get("solution_overview", "")
    components = data.get("core_components") or []
    steps = data.get("process_steps") or []
    effects = data.get("effects") or []
    terms = build_term_glossary(data)

    paragraphs = [
        _ensure_sentence(f"本发明的目的在于{problem}"),
        _ensure_sentence(f"为实现上述目的，本发明提出如下技术方案：{solution}"),
    ]

    bullets: List[str] = []
    if components:
        bullets.append(f"核心结构/模块包括：{_join_list(components)}。")
    if steps:
        bullets.extend([f"{idx + 1}. {step}" for idx, step in enumerate(steps)])
    if effects:
        bullets.append("与现有技术相比，本发明具有以下有益效果：")
        bullets.extend([f"{idx + 1}. {effect}" for idx, effect in enumerate(effects)])
    if terms:
        paragraphs.append("术语约定如下：")
        bullets.extend([f"{k}：{v}" for k, v in terms.items()])

    return SectionContent(title="发明内容", paragraphs=[p for p in paragraphs if p], bullets=bullets)


def _local_generate_drawings(data: Dict[str, Any]) -> SectionContent:
    drawings = data.get("drawings") or []
    if drawings:
        return SectionContent(title="附图说明", paragraphs=[], bullets=drawings)
    return SectionContent(title="附图说明", paragraphs=["本发明实施方式可选提供附图。"])


def _local_generate_embodiments(data: Dict[str, Any]) -> SectionContent:
    embodiments = data.get("embodiments", "")
    components = data.get("core_components") or []
    steps = data.get("process_steps") or []
    parameters = data.get("parameters", "")
    control_logic = data.get("control_logic", "")
    alternatives = data.get("alternatives", "")

    paragraphs = [
        "以下结合具体实施方式对本发明进行说明，但不构成对本发明的限制。",
        _ensure_sentence(embodiments),
    ]
    bullets: List[str] = []
    if components:
        bullets.append(f"关键组成：{_join_list(components)}。")
    if steps:
        bullets.append("流程步骤：")
        bullets.extend([f"{idx + 1}. {step}" for idx, step in enumerate(steps)])
    if parameters:
        bullets.append(f"关键参数：{parameters}。")
    if control_logic:
        bullets.append(f"控制逻辑：{control_logic}。")
    if alternatives:
        bullets.append(f"替换方案：{alternatives}。")
    return SectionContent(title="具体实施方式", paragraphs=[p for p in paragraphs if p], bullets=bullets)


def _local_generate_application(data: Dict[str, Any]) -> SectionContent:
    application = data.get("application_scenarios", "")
    paragraph = (
        _ensure_sentence(f"本发明适用于{application}")
        if application
        else "本发明可应用于多种行业场景，具有良好的适配性。"
    )
    return SectionContent(title="应用场景", paragraphs=[paragraph])


def generate_sections(
    data: Dict[str, Any],
    provider: Optional[Any],
    prompt_dir: Path,
    provider_config: Optional[Dict[str, Any]] = None,
) -> List[SectionContent]:
    provider_config = provider_config or {}
    if provider_config.get("rich_mode", True):
        sections = build_rich_sections(data)
    else:
        sections = [
            _local_generate_technical_field(data),
            _local_generate_background(data),
            _local_generate_invention_content(data),
            _local_generate_drawings(data),
            _local_generate_embodiments(data),
            _local_generate_application(data),
        ]
    if provider and provider_config.get("use_llm"):
        sections = _enhance_sections_with_llm(
            sections, data, provider, prompt_dir, provider_config
        )
    return sections
