from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Question:
    key: str
    label: str
    required: bool = False
    qtype: str = "text"  # text, list, dict
    help: Optional[str] = None
    default: Optional[Any] = None


QUESTIONS: List[Question] = [
    Question(
        key="title",
        label="专利题目",
        required=True,
        help="建议包含对象与用途，例如“用于XXX的YYY方法/装置”。",
    ),
    Question(
        key="technical_field",
        label="技术领域",
        required=True,
        help="描述所属技术领域与更具体的子领域。",
    ),
    Question(
        key="technical_field_detail",
        label="技术领域详细描述（可选）",
        required=False,
        help="可填写完整段落，优先作为技术领域正文。",
    ),
    Question(
        key="background",
        label="背景技术与现有问题",
        required=True,
        help="现有技术现状与存在的不足/痛点。",
    ),
    Question(
        key="background_status",
        label="现有技术现状（可选）",
        required=False,
        help="用于2.1现有技术现状，可填写完整段落。",
    ),
    Question(
        key="background_issues",
        label="现有技术存在的技术问题（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于2.2技术问题列表。",
    ),
    Question(
        key="problem_to_solve",
        label="发明要解决的技术问题",
        required=True,
        help="一句话或两句话明确问题。",
    ),
    Question(
        key="invention_purpose",
        label="发明目的（可选）",
        required=False,
        help="用于3.1发明目的，可填写完整段落。",
    ),
    Question(
        key="solution_overview",
        label="整体技术方案概述",
        required=True,
        help="概述核心思路与整体解决路径。",
    ),
    Question(
        key="core_components",
        label="关键结构/模块/部件（分号分隔）",
        required=True,
        qtype="list",
        help="例如：传感模块；控制模块；执行机构。",
    ),
    Question(
        key="core_components_detail",
        label="核心结构/模块详细说明（分号分隔，可选）",
        required=False,
        qtype="list",
        help="例如：数据分析模块：负责采集与清洗；决策模块：负责调度。",
    ),
    Question(
        key="process_steps",
        label="方法步骤或流程（分号分隔）",
        required=False,
        qtype="list",
        help="例如：S1采集数据；S2分析；S3输出控制。",
    ),
    Question(
        key="process_steps_detail",
        label="预测流程步骤详细说明（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于3.3.2详细步骤描述。",
    ),
    Question(
        key="control_logic",
        label="控制逻辑/算法要点",
        required=False,
        help="关键算法思路、判断逻辑或策略。",
    ),
    Question(
        key="parameters",
        label="关键参数范围或条件",
        required=False,
        help="可给出范围或典型取值。",
    ),
    Question(
        key="effects",
        label="有益效果/技术效果（分号分隔）",
        required=True,
        qtype="list",
        help="例如：降低能耗；提高精度；提升鲁棒性。",
    ),
    Question(
        key="effects_detail",
        label="有益效果详细说明（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于3.4有益效果详细条目。",
    ),
    Question(
        key="embodiments",
        label="实施例或应用场景描述",
        required=True,
        help="描述一个或多个实施例的流程与关键细节。",
    ),
    Question(
        key="implementation_preconditions",
        label="实施前提（可选）",
        required=False,
        help="用于5.1实施前提说明。",
    ),
    Question(
        key="implementation_steps_detail",
        label="具体实施步骤详细说明（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于5.2具体实施步骤。",
    ),
    Question(
        key="implementation_effects",
        label="实施效果（可选）",
        required=False,
        help="用于5.3实施效果描述。",
    ),
    Question(
        key="alternative_example",
        label="替换方案实施示例（可选）",
        required=False,
        help="用于5.4替换方案实施示例。",
    ),
    Question(
        key="drawings",
        label="附图名称（如有，分号分隔）",
        required=False,
        qtype="list",
        help="例如：图1为系统结构示意图；图2为流程图。",
    ),
    Question(
        key="drawings_notes",
        label="附图标记说明（可选）",
        required=False,
        help="例如：1-数据分析模块，2-决策模块等。",
    ),
    Question(
        key="application_scenarios",
        label="应用场景（如有）",
        required=False,
        help="例如：工业现场、医疗、仓储物流等。",
    ),
    Question(
        key="application_scenarios_list",
        label="应用场景列表（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于第六部分列表化场景描述。",
    ),
    Question(
        key="application_notes",
        label="应用场景补充说明（可选）",
        required=False,
        help="用于应用场景段落补充说明。",
    ),
    Question(
        key="alternatives",
        label="可替换方案/变形方案（如有）",
        required=False,
        help="描述可选实现或等效替换方式。",
    ),
    Question(
        key="alternatives_detail",
        label="替换方案详细说明（分号分隔，可选）",
        required=False,
        qtype="list",
        help="用于3.3.3替换方案条目。",
    ),
    Question(
        key="terms",
        label="关键术语定义（格式：术语=说明；术语=说明）",
        required=False,
        qtype="dict",
        help="用于术语一致性与歧义消除。",
    ),
]

REQUIRED_KEYS = [q.key for q in QUESTIONS if q.required]

SECTION_ORDER = [
    "技术领域",
    "背景技术",
    "发明内容",
    "附图说明",
    "具体实施方式",
    "应用场景",
]


def question_map() -> Dict[str, Question]:
    return {q.key: q for q in QUESTIONS}
