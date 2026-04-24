# runbook-copilot

面向工程团队的 RAG 事故排障助手 MVP。它不是通用聊天机器人，而是接收告警标题、服务名、日志片段和可选症状描述后，帮助工程师快速定位相关 runbook、历史事故、服务文档或 FAQ，并返回带引用的排障建议。

## 当前目标

- 从 `knowledge/` 下的本地 Markdown 文档导入知识。
- 按 Markdown 标题分块，提取标题、路径、文档类型、service 和 tags。
- 使用本地哈希向量 + SQLite 做最小向量检索。
- 使用 BM25 做关键词检索。
- 合并向量和 BM25 结果，并基于服务名、错误码、依赖名和 section 标题做简单 rerank。
- 提供反馈接口和离线 JSONL 评测脚本。

## 架构

```text
FastAPI routes
  -> services/incident_analyzer.py
  -> rag/retriever.py
  -> rag/vector_store.py + rag/bm25.py
  -> SQLite
```

核心目录：

- `app/api/routes`：HTTP API。
- `app/models`：Pydantic 请求和响应模型。
- `app/rag`：Markdown 分块、嵌入、向量存储、BM25 和混合检索。
- `app/services`：事故分析和反馈写入。
- `app/evaluation`：离线评测脚本和样例数据。
- `knowledge/`：本地知识库 Markdown。

## 本轮 MVP 决策

- 暂不接真实 LLM，先用可解释模板生成 grounded answer，确保引用来自检索结果。
- 向量检索使用确定性的哈希嵌入并存入 SQLite，避免首轮引入 Chroma/FAISS 的安装复杂度。后续可以替换为 Chroma、FAISS 或真实 embedding 模型。
- 不加入 Docker、认证、后台任务和外部告警系统集成。

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

- `entities`：提取出的服务、错误码和关键词。
- `rewrittenQuery`：用于检索的改写查询。
- `answer.summary`
- `answer.likelyCauses`
- `answer.steps`
- `answer.citations`
- `answer.nextAction`

### `POST /api/feedback`

记录用户对答案的评分和备注。

## 测试与评测

```bash
pytest
python -m app.evaluation.evaluate
```

运行评测前需要先导入知识：

```bash
python scripts/ingest.py
```

## 后续路线

- 接入真实 embedding 模型和 Chroma/FAISS。
- 接入 LLM 生成器，并强制答案只引用检索结果。
- 扩展 Markdown frontmatter 元数据解析。
- 增加历史事故数据集和 recall/precision 评测指标。
- 增加更细粒度的服务过滤、文档类型过滤和可解释 rerank reason。
