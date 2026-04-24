# AGENTS.md

## 项目定位

`runbook-copilot` 是面向工程团队的 RAG 事故排障助手。它不是通用聊天机器人。任何改动都应围绕“根据告警、服务名、日志和症状，检索知识库并生成带引用的排障建议”这个目标。

## 代码风格

- 使用 Python 3.11+。
- FastAPI 用于后端 API。
- Pydantic 用于请求和响应模型。
- SQLite 用于本地持久化。
- 函数保持短小、显式、易测试。
- 业务逻辑在函数入口尽早校验输入。
- 注释和文档使用中文；只有变量名、类型名和 API 字段保持英文。
- 避免不必要抽象，优先保留直接、可维护的实现。

## 工程边界

- MVP 阶段不引入 Docker。
- 不实现认证、RBAC、Grafana、Prometheus、PagerDuty 等真实集成。
- 不做前端，除非是为了验证 API 的极小 demo。
- 不引入后台 worker，除非同步实现已经明确不可用。
- 新依赖必须有明确收益，并写入 README。

## RAG 约束

- ingest 必须从 `knowledge/` 的 Markdown 文件读取。
- 分块策略以 Markdown heading 为主。
- 回答必须包含 citations，且 citation 必须来自检索结果。
- 如果没有命中文档，应明确说明知识库不足，而不是编造排障结论。
- 后续接入真实 LLM 时，必须保持 grounded answer，不允许无引用生成关键结论。

## 提交前检查

- 至少运行 `pytest`。
- 修改 API 时同步更新 README。
- 修改响应结构时同步更新 Pydantic schema 和相关测试。
