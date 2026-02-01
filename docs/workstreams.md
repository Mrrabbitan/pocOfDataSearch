# 可持续迭代方向

## 方向 1：提示词与模板优化
- 目标：提升生成质量与一致性
- 关联路径：`prompts/`、`templates/disclosure.docx`
- 可做事项：分领域模板、版本记录、结构化提示词

## 方向 2：测试与示例完善
- 目标：提高稳定性与回归覆盖
- 关联路径：`tests/`、`tests/fixtures/`
- 可做事项：新增边界用例、多领域示例、集成测试

## 方向 3：Web 体验改进
- 目标：提高可用性与反馈清晰度
- 关联路径：`web_templates/index.html`、`static/styles.css`、`src/web/app.py`
- 可做事项：表单校验、错误提示、移动端布局

## 方向 4：配置与核心逻辑演进
- 目标：提升可扩展性与可维护性
- 关联路径：`src/config/config.yaml`、`src/core/`
- 可做事项：配置预设、字段校验、可选参数说明
