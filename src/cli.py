from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from .core.checks import check_required_fields, run_checks
from .core.generator import generate_sections
from .core.intake import collect_inputs, normalize_inputs
from .core.utils import safe_filename
from .llm.provider import load_provider
from .render.docx import render_docx


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_input_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"未找到输入文件：{path}")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError("仅支持 .json/.yaml/.yml 输入文件")


def resolve_output_path(output: str | None, title: str) -> Path:
    if not output:
        return Path("outputs") / f"{safe_filename(title)}.docx"
    path = Path(output)
    if path.exists() and path.is_dir():
        return path / f"{safe_filename(title)}.docx"
    if path.suffix.lower() != ".docx":
        return path.with_suffix(".docx")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="专利交底书生成器")
    parser.add_argument("--title", help="专利题目")
    parser.add_argument("--input", help="输入文件（json/yaml）")
    parser.add_argument("--output", help="输出 .docx 路径")
    parser.add_argument(
        "--config",
        default="src/config/config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="非交互模式（需要提供完整输入）",
    )
    parser.add_argument(
        "--use-template",
        action="store_true",
        help="使用模板文件进行渲染",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)

    data: Dict[str, Any] = {}
    if args.input:
        data.update(load_input_file(Path(args.input)))
    if args.title:
        data["title"] = args.title

    if args.non_interactive:
        data = normalize_inputs(data)
        missing = check_required_fields(data)
        if missing:
            print("输入缺少必填字段：")
            for issue in missing:
                print(f"- {issue}")
            return 2
    else:
        data = collect_inputs(data)

    prompt_dir = Path(config.get("prompt_dir", "prompts"))
    provider = load_provider(config)
    sections = generate_sections(data, provider, prompt_dir, config)

    issues = run_checks(data, sections)
    output_path = resolve_output_path(args.output, data.get("title", "交底书"))
    template_path = Path(config.get("template_path", "templates/disclosure.docx"))
    render_docx(
        sections,
        output_path=output_path,
        template_path=template_path,
        use_template=args.use_template or bool(config.get("use_template")),
    )

    print(f"已生成交底书：{output_path}")
    if issues:
        print("一致性检查提示：")
        for issue in issues:
            print(f"- {issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
