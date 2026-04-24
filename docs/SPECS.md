# SPEC.md

## 1. 项目名称

**Runbook Copilot**

副标题：**面向工程排障场景的 RAG 助手**

---

## 2. 项目目标

构建一个面向工程团队的排障辅助系统。
当用户输入告警标题、服务名、日志片段或异常描述时，系统能够：

1. 提取关键实体
2. 将输入改写为更适合检索的查询
3. 在本地知识库中执行混合检索
4. 基于检索结果生成结构化排障建议
5. 返回引用来源，确保回答可追溯
6. 支持基础反馈与离线评估

本项目**不是通用聊天机器人**，而是一个专注于 **incident / runbook / troubleshooting** 场景的 AI 工具。

---

## 3. 背景与问题定义

许多工程团队已经沉淀了 runbook、FAQ、服务说明、事故复盘等文档，但在真实故障发生时仍然面临这些问题：

* 告警来了之后，不知道该优先查哪份文档
* 日志片段中包含大量关键词，但检索结果不稳定
* 仅使用向量检索时，对错误码、类名、服务名等精确信息支持不足
* 直接让大模型自由回答，容易出现幻觉，可信度不足
* 缺少结构化、可执行的排障建议输出

本项目的目标是：
**把日志 / 告警 / 异常描述，转换成一个面向工程排障的检索增强流程。**

---

## 4. 产品定位

### 4.1 核心定位

一个 **RAG-based incident troubleshooting assistant**。

### 4.2 核心价值

* 帮助工程师更快定位相关 runbook 和历史案例
* 提供结构化排障建议，而不是泛泛问答
* 通过 citation 降低幻觉风险
* 作为后续接入监控告警系统的基础能力层

### 4.3 非目标

本项目当前阶段不追求：

* 自动执行运维命令
* 多 Agent 协同
* 全功能 SRE 平台
* 实时日志流处理
* 企业级权限管理
* 精美前端交互

---

## 5. MVP 范围

### 5.1 输入

MVP 仅支持以下输入字段：

* `alert_title`：告警标题
* `service_name`：服务名
* `log_snippet`：日志片段
* `symptom`：补充症状描述（可选）

### 5.2 输出

MVP 输出为结构化 JSON，至少包含：

* `summary`：问题摘要
* `likely_causes`：可能原因列表
* `steps`：建议排查步骤
* `citations`：引用来源列表
* `next_action`：下一步建议动作

### 5.3 知识来源

MVP 使用本地 markdown 文档作为知识源，类型包括：

* runbooks
* incidents
* services
* faq

---

## 6. 用户故事

### 6.1 主用户故事

作为一名工程师，
当我收到一条告警或看到一段报错日志时，
我希望系统能快速给我找到最相关的 runbook 和历史故障案例，
并生成可信的排查建议，
从而减少人工搜索和定位时间。

### 6.2 典型场景

#### 场景 A：数据库连接池耗尽

输入：

* alert_title: `payment-service error spike`
* service_name: `payment-service`
* log_snippet: `remaining connection slots are reserved`
* symptom: `5xx errors increased after latest deployment`

期望：

* 识别 PostgreSQL / connection exhaustion 等实体
* 检索到数据库连接耗尽相关 runbook
* 给出检查连接池、活跃 session、长事务的步骤
* 引用对应文档路径

#### 场景 B：缓存连接失败

输入：

* service_name: `order-service`
* log_snippet: `redis connection refused`

期望：

* 识别 Redis 依赖异常
* 检索到缓存不可用或连接失败类 runbook
* 输出检查缓存实例状态、网络连通性、配置变更的步骤

---

## 7. 功能需求

## 7.1 Knowledge Ingestion

系统需要支持从本地 `knowledge/` 目录扫描并导入 markdown 文档。

### 要求

* 读取 markdown 文件
* 按标题进行分块
* 为每个 chunk 建立 metadata
* 建立向量索引
* 建立关键词索引

### metadata 至少包括

* 文档标题
* 文档类型
* 文件路径
* chunk id
* section 标题

---

## 7.2 Incident Input API

系统需要提供一个 HTTP API，用于接收 incident 分析请求。

### 请求字段

* `alert_title`
* `service_name`
* `log_snippet`
* `symptom`

### 行为要求

* 对输入做基础校验
* 对空输入或无效输入返回明确错误
* 所有请求返回结构化响应

---

## 7.3 Entity Extraction

系统需要从用户输入中提取工程排障相关实体。

### 至少包括

* service
* dependency
* exception type
* error code
* keywords
* symptom tags

### 目标

帮助后续检索更精确，而不是直接拿原始日志做检索。

---

## 7.4 Query Rewrite

系统需要将原始 incident 输入改写为更适合检索的查询。

### 输出建议

* `keyword_query`
* `semantic_query`
* `filters`（可选）

### 目标

提升 BM25 与 vector retrieval 的召回效果。

---

## 7.5 Hybrid Retrieval

系统需要同时使用：

* 关键词检索
* 向量检索

并对两路结果进行合并与排序。

### 最低要求

* BM25 top-k
* Vector top-k
* merge
* rule-based rerank

### 设计目标

避免只依赖 embedding，提升对以下信息的支持：

* 服务名
* 错误码
* 类名
* 中间件名
* 精确异常描述

---

## 7.6 Answer Synthesis

系统需要基于召回文档生成结构化排障建议。

### 约束

* 回答必须尽量基于召回证据
* 无法确定时要明确表示不确定
* 必须返回 citation
* 输出必须符合 response schema

### 目标

让结果更适合工程排障，而不是普通自然语言问答。

---

## 7.7 Feedback

系统需要提供反馈接口，支持记录用户对结果的评价。

### 支持的反馈值

* `useful`
* `partially_useful`
* `not_useful`

### MVP 目标

第一版仅做存储，不做在线学习。

---

## 7.8 Offline Evaluation

系统需要支持离线评估。

### 最低要求

准备一份 JSONL 数据集，每条样本包含：

* 输入内容
* 期望命中的文档
* 期望关键词或异常类型

### 初始指标

* retrieval hit@3
* retrieval hit@5
* citation relevance
* answer usefulness
* schema validity

---

## 8. 非功能需求

### 8.1 可维护性

* 代码需分层明确
* 函数职责单一
* 尽量避免过早抽象
* 核心流程清晰可追踪

### 8.2 可扩展性

* 后续可以接入真实监控平台
* 后续可以替换模型提供商
* 后续可以替换向量库
* 后续可以增加 reranker 或多阶段检索

### 8.3 可解释性

* 每次回答都应可追溯到引用文档
* 检索与生成流程要易于调试

### 8.4 本地可运行

* 项目第一版必须支持本地独立运行
* 不依赖复杂云基础设施
* 优先保证开发体验和迭代效率

---

## 9. 技术约束

### 9.1 编程语言

* Python 3.11+

### 9.2 Web Framework

* FastAPI

### 9.3 数据模型

* Pydantic

### 9.4 存储

* SQLite

### 9.5 检索

* BM25
* Local vector store（如 Chroma / FAISS）

### 9.6 测试

* pytest

### 9.7 依赖原则

* 优先使用轻量、成熟、易维护的依赖
* 避免在 MVP 阶段引入不必要的基础设施

---

## 10. 推荐架构

### 10.1 总体流程

...text
User Input
-> Incident API
-> Entity Extraction
-> Query Rewrite
-> Hybrid Retrieval
-> BM25 Retriever
-> Vector Retriever
-> Merge + Rerank
-> Answer Synthesis
-> Structured Response with Citations
-> Feedback / Evaluation
...

### 10.2 分层设计

#### API Layer

负责：

* 接收 HTTP 请求
* 调用 application/service 层
* 返回标准响应

#### Application / Service Layer

负责：

* incident 分析主流程编排
* 各子模块串联
* 控制业务流程

#### Knowledge / Retrieval Layer

负责：

* markdown 加载
* chunking
* metadata enrichment
* index building
* BM25 / vector retrieval
* hybrid retrieval

#### LLM Layer

负责：

* entity extraction prompt
* query rewrite prompt
* answer synthesis prompt
* structured output parsing
* 模型适配

#### Storage Layer

负责：

* SQLite 存 feedback / metadata
* vector store 持久化

#### Evaluation Layer

负责：

* 数据集加载
* hit@k 计算
* relevance 评估
* answer usefulness 评估辅助

---

## 11. 目录结构规范

...text
runbook-copilot/
app/
api/
routes/
health.py
ingest.py
incidents.py
feedback.py
core/
config.py
logging.py
models/
incident.py
document.py
response.py
feedback.py
services/
ingestion_service.py
entity_extraction_service.py
query_rewrite_service.py
retrieval_service.py
ranking_service.py
answer_service.py
feedback_service.py
rag/
chunking.py
metadata.py
bm25_index.py
vector_index.py
hybrid_retriever.py
llm/
client.py
prompts.py
schemas.py
evaluation/
dataset_loader.py
evaluator.py
metrics.py
main.py

knowledge/
runbooks/
incidents/
services/
faq/

data/
eval_cases.jsonl
app.db

tests/
test_chunking.py
test_entity_extraction.py
test_retrieval.py
test_answer_schema.py

scripts/
ingest_knowledge.py
run_eval.py

AGENTS.md
README.md
requirements.txt
.env.example
...

---

## 12. API 规范

## 12.1 健康检查

### `GET /api/health`

返回：

* 服务状态
* 版本信息（可选）

---

## 12.2 导入知识库

### `POST /api/knowledge/ingest`

行为：

* 扫描 `knowledge/`
* 读取 markdown
* chunk
* 建索引
* 返回导入统计信息

响应示例：

* 文档数量
* chunk 数量
* 成功 / 失败数量

---

## 12.3 Incident 分析

### `POST /api/incidents/analyze`

请求示例：

...json
{
"alert_title": "PaymentService error rate > 20%",
"service_name": "payment-service",
"log_snippet": "org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved...",
"symptom": "recent spike in 5xx errors after deployment"
}
...

响应示例：

...json
{
"summary": "Likely database connection exhaustion in payment-service.",
"likely_causes": [
"Connection pool saturation",
"Long-running transactions",
"Unreleased DB connections after recent deployment"
],
"steps": [
"Check DB connection pool usage",
"Inspect active sessions in PostgreSQL",
"Compare recent deployment changes",
"Review application logs for connection leak patterns"
],
"citations": [
{
"title": "Payment DB Timeout Runbook",
"path": "knowledge/runbooks/payment-db-timeout.md"
}
],
"next_action": "Verify whether connection pool usage increased after the latest release."
}
...

---

## 12.4 反馈接口

### `POST /api/feedback`

请求字段建议：

* request id
* feedback type
* optional comment

---

## 13. 数据模型

## 13.1 IncidentQuery

...json
{
"alert_title": "string",
"service_name": "string",
"log_snippet": "string",
"symptom": "string"
}
...

## 13.2 ExtractedContext

...json
{
"service": "string",
"dependencies": ["string"],
"exception_types": ["string"],
"error_codes": ["string"],
"keywords": ["string"],
"symptoms": ["string"]
}
...

## 13.3 RetrievedDocument

...json
{
"id": "string",
"title": "string",
"source_type": "runbook|incident|service|faq",
"path": "string",
"score": 0.0,
"snippet": "string"
}
...

## 13.4 CopilotResponse

...json
{
"summary": "string",
"likely_causes": ["string"],
"steps": ["string"],
"citations": [
{
"title": "string",
"path": "string"
}
],
"next_action": "string"
}
...

---

## 14. Prompt 设计要求

为保证流程稳定，Prompt 需按职责拆分，而不是单次大 Prompt。

## 14.1 Entity Extraction Prompt

目标：

* 从告警 / 日志中抽关键实体
* 输出结构化 JSON

## 14.2 Query Rewrite Prompt

目标：

* 将 incident 输入改写为适合检索的 keyword / semantic query

## 14.3 Answer Synthesis Prompt

目标：

* 基于召回文档生成结构化排障建议

约束：

* 仅基于证据回答
* 保留不确定性
* 必须输出 citation
* 必须符合 schema

---

## 15. 检索设计要求

## 15.1 Chunking

* 优先按 markdown 标题切分
* section 过长时再细分
* 保持 chunk 与 section 的语义一致性

## 15.2 Retrieval

* BM25 与 vector retrieval 并行执行
* 合并召回结果
* 进入 rerank 阶段

## 15.3 初版 Rerank 规则

可采用简单规则打分：

* 同 service 加分
* 同 exception 加分
* 同 dependency 加分
* runbook 类型加分
* incident case 类型加分

---

## 16. 测试要求

MVP 至少需要包含以下测试：

* `test_chunking.py`
* `test_entity_extraction.py`
* `test_retrieval.py`
* `test_answer_schema.py`

### 测试目标

* chunking 输出合理
* retrieval 至少能召回目标文档
* response schema 合法
* 基础流程可运行

---

## 17. 评估要求

## 17.1 数据集

准备 `data/eval_cases.jsonl`

每条样本建议包含：

* id
* alert_title
* service_name
* log_snippet
* symptom
* expected_docs
* expected_keywords

## 17.2 指标

MVP 阶段至少统计：

* hit@3
* hit@5
* citation relevance
* useful response rate
* format validity

## 17.3 评估目标

第一版不追求绝对高分，重点是：

* 建立评估闭环
* 能比较不同检索策略
* 能支持后续迭代优化

---

## 18. 开发阶段规划

## Phase 1：基础骨架

目标：

* 初始化 FastAPI 项目
* 实现 `/api/health`
* 完成基础配置与项目结构

交付物：

* 可运行的服务骨架
* README 初版
* AGENTS.md 初版

---

## Phase 2：知识导入与基础检索

目标：

* 读取 markdown
* chunk
* 建立 vector index
* 提供基本检索能力

交付物：

* `/api/knowledge/ingest`
* ingestion script
* retrieval 初版

---

## Phase 3：Hybrid Retrieval

目标：

* 加入 BM25
* 合并 keyword/vector 结果
* 简单 rerank

交付物：

* hybrid retriever
* retrieval tests

---

## Phase 4：Incident Analysis

目标：

* entity extraction
* query rewrite
* answer generation
* citation 输出

交付物：

* `/api/incidents/analyze`
* response schema
* 基础可用的排障结果

---

## Phase 5：反馈与评估

目标：

* feedback API
* eval dataset
* eval script

交付物：

* `/api/feedback`
* `run_eval.py`
* README 中加入评估说明

---

## 19. Definition of Done

第一版完成标准：

1. 项目可本地启动
2. `/api/health` 可用
3. `/api/knowledge/ingest` 可导入本地 markdown 文档
4. `/api/incidents/analyze` 能返回结构化 JSON
5. 系统已实现基础 hybrid retrieval
6. 回答中包含 citation
7. 仓库包含 README 与 AGENTS.md
8. 至少有基础测试与离线评估脚本
9. 项目结构可支持下一阶段迭代

---

## 20. 开发原则

* 优先最小可运行实现
* 不做过度设计
* 不提前引入复杂基础设施
* 函数入口先校验输入
* 尽量写类型明确、职责单一的代码
* 优先保证检索质量与引用可信度
* 当需求有歧义时，优先做合理 MVP 决策，并写入 README

---

## 21. 后续迭代方向

MVP 完成后，可考虑继续扩展：

* 接入真实监控平台
* 接入真实告警事件源
* 增加 reranker
* 增加历史 case clustering
* 增加多轮交互
* 增加 query routing
* 增加前端界面
* 增加模型对比与 prompt versioning
* 增加更完整的反馈闭环

---

## 22. 一句话总结

Runbook Copilot 的第一版，不追求“万能 AI 助手”，而是专注于一个清晰的工程场景：

**把告警、日志和异常描述，转化为带引用的结构化排障建议。**
