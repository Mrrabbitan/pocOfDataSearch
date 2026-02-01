from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.checks import check_required_fields, run_checks
from ..core.generator import SectionContent, generate_sections
from ..core.intake import normalize_inputs
from ..core.schema import QUESTIONS, Question
from ..core.utils import safe_filename
from ..llm.provider import load_provider

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "web_templates"
SAMPLE_PATH = ROOT / "tests" / "fixtures" / "sample_input.json"

app = FastAPI(title="专利交底书生成器")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_sample_data() -> Dict[str, Any]:
    if not SAMPLE_PATH.exists():
        return {}
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


def format_value_for_form(value: Any, question: Question) -> str:
    if value is None:
        return ""
    if question.qtype == "list":
        if isinstance(value, list):
            return "；".join([str(item) for item in value])
        return str(value)
    if question.qtype == "dict":
        if isinstance(value, dict):
            return "；".join([f"{k}={v}" for k, v in value.items()])
        return str(value)
    return str(value)


def build_grouped_questions() -> List[Dict[str, Any]]:
    group_keys = [
        {
            "title": "基础信息",
            "keys": ["title", "technical_field", "background", "problem_to_solve"],
        },
        {
            "title": "方案与结构",
            "keys": [
                "solution_overview",
                "core_components",
                "process_steps",
                "control_logic",
                "parameters",
                "effects",
            ],
        },
        {
            "title": "实施与附图",
            "keys": [
                "embodiments",
                "drawings",
                "application_scenarios",
                "alternatives",
                "terms",
            ],
        },
        {
            "title": "高级扩展（可选）",
            "keys": [
                "technical_field_detail",
                "background_status",
                "background_issues",
                "invention_purpose",
                "core_components_detail",
                "process_steps_detail",
                "alternatives_detail",
                "effects_detail",
                "drawings_notes",
                "implementation_preconditions",
                "implementation_steps_detail",
                "implementation_effects",
                "alternative_example",
                "application_scenarios_list",
                "application_notes",
            ],
            "collapsible": True,
        },
    ]
    question_map = {q.key: q for q in QUESTIONS}
    groups: List[Dict[str, Any]] = []
    for group in group_keys:
        keys = group["keys"]
        items = [question_map[key] for key in keys if key in question_map]
        groups.append(
            {
                "title": group["title"],
                "questions": items,
                "collapsible": group.get("collapsible", False),
            }
        )
    return groups


def resolve_output_path(title: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = safe_filename(title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{base}_{timestamp}.docx"


def _render_index(
    request: Request,
    data: Optional[Dict[str, Any]] = None,
    sections: Optional[List[SectionContent]] = None,
    issues: Optional[List[str]] = None,
    error: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    config = config or {}
    data = data or {}
    issues = issues or []
    groups = build_grouped_questions()
    download_name = data.get("download_name", "")
    form_values = {
        q.key: format_value_for_form(data.get(q.key), q) for q in QUESTIONS
    }
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "groups": groups,
            "form_values": form_values,
            "download_name": download_name,
            "sections": sections,
            "issues": issues,
            "error": error,
            "web_title": config.get("web_title", "专利交底书生成器"),
            "provider": config.get("provider", "template"),
            "use_template": bool(config.get("use_template")),
        },
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request, sample: int = 0) -> HTMLResponse:
    config = load_config(ROOT / "src" / "config" / "config.yaml")
    data = load_sample_data() if sample else {}
    return _render_index(request, data=data, config=config)


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request) -> HTMLResponse:
    config = load_config(ROOT / "src" / "config" / "config.yaml")
    try:
        form = await request.form()
        raw_data = {k: v for k, v in form.items()}
        data = normalize_inputs(raw_data)
        missing = check_required_fields(data)
        if missing:
            return _render_index(
                request,
                data=data,
                issues=missing,
                error="必填字段未完整填写。",
                config=config,
            )

        provider = load_provider(config)
        prompt_dir = Path(config.get("prompt_dir", "prompts"))
        sections = generate_sections(data, provider, prompt_dir, config)
        issues = run_checks(data, sections)

        output_dir = ROOT / config.get("output_dir", "outputs")
        output_path = resolve_output_path(data.get("title", "交底书"), output_dir)
        from ..render.docx import render_docx

        render_docx(
            sections,
            output_path=output_path,
            template_path=Path(config.get("template_path", "templates/disclosure.docx")),
            use_template=bool(config.get("use_template")),
        )
        data["download_name"] = output_path.name
        return _render_index(
            request,
            data=data,
            sections=sections,
            issues=issues,
            config=config,
        )
    except Exception as exc:
        return _render_index(
            request,
            data={},
            sections=None,
            issues=[],
            error=f"生成失败：{exc}",
            config=config,
        )


@app.get("/download/{filename}")
def download(filename: str) -> FileResponse:
    config = load_config(ROOT / "src" / "config" / "config.yaml")
    output_dir = ROOT / config.get("output_dir", "outputs")
    safe_name = Path(filename).name
    if not safe_name.endswith(".docx"):
        raise FileNotFoundError("不支持的文件格式")
    path = output_dir / safe_name
    if not path.exists():
        raise FileNotFoundError("文件不存在")
    return FileResponse(path, filename=safe_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
