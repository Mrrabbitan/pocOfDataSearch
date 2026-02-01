# 专利交底书生成器

本项目用于生成中文专利交底书，支持 CLI 与 Web 两种方式运行，默认模板生成（可配置 LLM）。

## 本地部署与运行

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 启动 Web 页面

```bash
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
```

浏览器访问：`http://localhost:8000`

### 3) 使用 CLI

交互式：

```bash
python -m src.cli --title "一种用于仓储物流的智能预测模型构建方法"
```

非交互式（示例输入）：

```bash
python -m src.cli --input tests/fixtures/sample_input.json --non-interactive
```

## 配置说明

配置文件位于 `src/config/config.yaml`，可配置：

- `provider`：`template`（默认）或 `openai`
- `model`：LLM 模型名称
- `prompt_dir`：提示词目录
- `template_path`：docx 模板
- `rich_mode`：是否启用分层结构生成（默认开启）
- `use_llm`：是否用 LLM 进行补充生成（默认关闭）
- `output_dir`：输出目录
- `web_title`：Web 页面标题

## Web 页面规划（内置实现）

- 左侧为输入区：按“基础信息 / 方案与结构 / 实施与附图 / 高级扩展”四组分区输入
- 右侧为结果区：展示生成预览与下载入口
- 顶部提供示例填充按钮与当前模式提示
