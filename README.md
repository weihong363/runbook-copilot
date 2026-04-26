# runbook-copilot

面向工程团队的 RAG 事故排障助手 MVP。它不是通用聊天机器人，而是接收告警标题、服务名、日志片段和可选症状描述后，帮助工程师快速定位相关 runbook、历史事故、服务文档或 FAQ，并返回带引用的排障建议。

## 当前目标

- 从 `knowledge/` 下的本地 Markdown 文档导入知识。
- 按 Markdown 标题分块，提取标题、路径、文档类型、service 和 tags。
- 使用本地哈希向量 + SQLite 做最小向量检索。
- 使用 BM25 做关键词检索。
- 合并向量和 BM25 结果，并基于服务名、错误码、依赖名和 section 标题做简单 rerank。
- 默认使用模板生成 grounded answer，可选接入 OpenAI 做受 citation 约束的回答合成。
- 提供通用告警事件入口、incident 本地留存、反馈接口和离线 JSONL 评测脚本。

## 架构

```text
FastAPI routes
  -> services/incident_analyzer.py
  -> rag/retriever.py
  -> rag/vector_store.py + rag/bm25.py
  -> llm/answer_generator.py
  -> services/incident_store.py + services/feedback_service.py
  -> SQLite
```

核心目录：

- `app/api/routes`：HTTP API。
- `app/models`：Pydantic 请求和响应模型。
- `app/rag`：Markdown 分块、嵌入、向量存储、BM25 和混合检索。
- `app/llm`：模板回答、可选 LLM 回答生成、prompt version 和 citation 绑定。
- `app/services`：事故分析和反馈写入。
- `app/static/debug.html`：极简 API 调试页面。
- `app/evaluation`：离线评测脚本和样例数据。
- `knowledge/`：本地知识库 Markdown。

## 本轮 MVP 决策

- 默认用可解释模板生成 grounded answer，确保离线可运行。
- 可选接入 OpenAI Responses API 做 answer synthesis，但仍强制答案 citation 来自检索结果。
- 向量检索使用确定性的哈希嵌入并存入 SQLite，避免首轮引入 Chroma/FAISS 的安装复杂度。后续可以替换为 Chroma、FAISS 或真实 embedding 模型。
- Milestone 10 只提供通用事件入口，不接具体 Grafana / Prometheus / PagerDuty SDK。
- 不加入 Docker、认证、后台任务。

## 本地运行

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

导入知识：

```bash
python scripts/ingest.py
```

或通过 API：

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/ingest
```

## API

### `GET /api/health`

返回服务健康状态。

### `POST /api/knowledge/ingest`

读取 `knowledge/` 下的 Markdown 文件并重建本地索引。

响应还会包含：

- `indexedByDocType`：按文档类型统计的导入数量
- `emptySectionsMerged`：被合并的超短小节数量

### `POST /api/incidents/analyze`

请求示例：

```json
{
  "alertTitle": "checkout-api HTTP 500 错误率升高",
  "serviceName": "checkout-api",
  "logSnippet": "HTTP 500 DB_POOL_EXHAUSTED timeout acquiring connection",
  "symptomDescription": "下单接口大量失败"
}
```

响应包含：

- `incidentId`
- `entities`：提取出的服务、依赖、异常类型、错误码、关键词和症状标签。
- `rewrittenQuery.keywordQuery`：用于 BM25 的关键词检索查询。
- `rewrittenQuery.semanticQuery`：用于向量召回的语义查询。
- `rewrittenQuery.filters`：用于服务名和文档类型约束的过滤条件。
- `answer.summary`
- `answer.likelyCauses`
- `answer.steps`
- `answer.citations`
- `answer.nextAction`

回答层当前行为：

- 只在召回证据足够强时给出明确排障起点
- 当只命中弱相关资料时，会明确标注“只是初步线索”
- citation excerpt 会去掉 markdown 标题行，保留更稳定的正文片段
- LLM 生成路径会二次校验 citations，只保留本次检索返回的 chunk

分析结果会写入本地 SQLite 的 `incidents` 表，方便后续反馈和排查回看。

### `POST /api/incidents/events`

通用告警事件入口，给真实告警系统或脚本调用。当前不绑定具体平台，只接收标准化事件：

```json
{
  "sourceType": "grafana-webhook",
  "sourceId": "alert-123",
  "alertTitle": "checkout-api HTTP 500 错误率升高",
  "serviceName": "checkout-api",
  "logSnippet": "HTTP 500 DB_POOL_EXHAUSTED timeout acquiring connection",
  "severity": "critical",
  "labels": {
    "team": "checkout"
  }
}
```

该接口会复用 analyze 主流程，并把来源信息写入 incident 记录。

### `POST /api/incidents/integrations/grafana`

接收 Grafana Alerting / Alertmanager 风格 webhook payload，并将每条 `firing` alert 转成 incident event。

当前支持：

- `alerts[].labels.service` / `job` / `app` 映射为 `serviceName`
- `alerts[].labels.alertname` 映射为告警名
- `annotations.description` / `message` 映射为 `logSnippet`
- `annotations.summary` 映射为 `symptomDescription`
- `fingerprint` / `groupKey` 映射为 `sourceId`
- `resolved` alert 会被跳过

如果设置 `GRAFANA_WEBHOOK_SECRET`，接口会校验 Grafana HMAC 签名。

### `GET /api/incidents`

返回最近分析过的 incident：

```bash
curl "http://127.0.0.1:8000/api/incidents?limit=20"
```

### `GET /api/incidents/{incidentId}`

返回单个 incident 的来源、基本信息和已生成答案。

### `POST /api/feedback`

记录用户对答案的评分和备注。

请求示例：

```json
{
  "incidentId": "inc_xxx",
  "rating": 4,
  "useful": true,
  "reason": "hit",
  "comment": "命中文档正确"
}
```

### `GET /api/feedback`

按时间倒序返回反馈记录，支持按 incident 过滤：

```bash
curl "http://127.0.0.1:8000/api/feedback?incidentId=inc_xxx"
```

### `GET /api/feedback/summary`

返回反馈总数、平均分、有用/无用数量：

```bash
curl "http://127.0.0.1:8000/api/feedback/summary?incidentId=inc_xxx"
```

## 测试与评测

```bash
pytest
python -m app.evaluation.evaluate
```

评测脚本会自动重新 ingest 当前 `knowledge/`，然后输出一份结构化 JSON 报告，包含：

- `summary.hitAt3`：期望文档是否进入前 3 个 citation
- `summary.hitAt5`：期望文档是否进入前 5 个 citation
- `summary.citationRelevance`：首个 citation 是否就是期望文档
- `summary.schemaValidity`：回答是否通过 response schema 校验
- `summary.answerUsefulness`：答案是否同时满足结构完整、citation 相关和可执行步骤数量
- `summary.keywordCoverage`：期望关键词在 `rewrittenKeywordQuery` 中的覆盖比例

每个 case 还会输出：

- 期望命中文档
- 实际 citation 列表
- `rewrittenKeywordQuery`
- `rewrittenSemanticQuery`

解读建议：

- `hitAt3` 下降，通常优先检查 query rewrite、service filter 或 rerank
- `hitAt5` 正常但 `citationRelevance` 下降，通常说明召回还在，但排序变差
- `keywordCoverage` 下降，通常说明 incident 输入理解或 query rewrite 退化
- `schemaValidity` 不为 `1.0`，说明回答层或 response schema 出现回归
- `answerUsefulness` 下降，通常优先检查生成层是否丢失步骤、nextAction 或有效引用

## 知识库规范

知识文档编写规范在：

- [KNOWLEDGE_STYLE_GUIDE.md](/Users/ironion/workspace/runbook-copilot/docs/KNOWLEDGE_STYLE_GUIDE.md)

可复用模板在：

- [runbook_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/runbook_template.md)
- [incident_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/incident_template.md)
- [service_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/service_template.md)
- [faq_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/faq_template.md)

知识库 lint：

```bash
python scripts/lint_knowledge.py
```

这个脚本会检查标题、tags、文档类型、二级标题和 service 提取情况。

## 调试

分析接口支持可选 debug 开关：

```json
{
  "alertTitle": "checkout-api HTTP 500",
  "serviceName": "checkout-api",
  "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
  "debug": true
}
```

开启后，响应会额外返回：

- `debug.entities`
- `debug.rewrittenQuery`
- `debug.retrieval.candidates`
- `debug.retrieval.stages`
- 每个候选文档的 `vectorScore`、`bm25Score`、`rerankBoost`、`finalScore` 和 `rerankReasons`

排查步骤见：

- [DEBUG_CHECKLIST.md](/Users/ironion/workspace/runbook-copilot/docs/DEBUG_CHECKLIST.md)
- [RERANKER_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/RERANKER_DECISION.md)

也可以打开极简调试页面：

```text
http://127.0.0.1:8000/debug
```

该页面只用于本地 API 验证，不是正式前端。

## 向量与 Embedding

默认配置继续使用本地 `sqlite + hash embedding`，保证离线可运行：

```env
VECTOR_STORE_BACKEND=sqlite
EMBEDDING_PROVIDER=hash
VECTOR_DIMENSION=128
```

如果要试验真实本地 embedding，可安装可选依赖：

```bash
pip install -r requirements-embeddings.txt
EMBEDDING_PROVIDER=sentence-transformers python -m app.evaluation.evaluate
```

比较不同 provider 的评测结果：

```bash
python scripts/compare_vector_configs.py
```

当前决策记录见：

- [VECTOR_BACKEND_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/VECTOR_BACKEND_DECISION.md)

## 回答生成

默认配置使用模板生成，保证本地无外部依赖即可运行：

```env
ANSWER_GENERATOR=template
ANSWER_PROMPT_VERSION=grounded-v1
```

如果要试验真实 LLM 回答合成，可安装可选依赖并配置 OpenAI API key：

```bash
pip install -r requirements-llm.txt
ANSWER_GENERATOR=openai OPENAI_MODEL=gpt-5.2 python -m app.evaluation.evaluate
```

比较模板生成和 LLM 生成的评测结果：

```bash
python scripts/compare_answer_generators.py
```

如果未安装 `openai` 或缺少 API key，脚本会把 `openai` 标记为 `skipped`，不会影响默认模板路径。

当前决策记录见：

- [ANSWER_GENERATION_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/ANSWER_GENERATION_DECISION.md)

## 产品化扩展

Milestone 10 已加入最小产品闭环：

- `POST /api/incidents/events`：通用告警事件入口
- `GET /api/incidents` / `GET /api/incidents/{incidentId}`：incident 本地留存和回看
- `POST /api/feedback`：支持 `useful` 和 `reason`
- `GET /api/feedback` / `GET /api/feedback/summary`：反馈列表和汇总
- `GET /debug`：极简本地调试页面

当前决策记录见：

- [PRODUCTIZATION_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/PRODUCTIZATION_DECISION.md)

公开事故样本回放记录见：

- [REAL_WORLD_SAMPLE_REPLAY.md](/Users/ironion/workspace/runbook-copilot/docs/REAL_WORLD_SAMPLE_REPLAY.md)
- [WEBHOOK_INTEGRATION_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/WEBHOOK_INTEGRATION_DECISION.md)

## 后续路线

- 在评测证明有收益后，再接入 Chroma/FAISS。
- 扩展 LLM 生成评测集，并在 usefulness 明确提升后再切默认生成器。
- 接入具体告警平台前，先稳定通用事件 schema 和 feedback 指标。
- 扩展 Markdown frontmatter 元数据解析。
- 增加历史事故数据集和 recall/precision 评测指标。
- 增加更细粒度的服务过滤、文档类型过滤和可解释 rerank reason。
