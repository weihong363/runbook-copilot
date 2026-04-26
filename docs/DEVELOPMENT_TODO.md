# Runbook Copilot 开发清单

这份清单基于 `docs/SPECS.md` 和当前仓库状态整理，目标是把后续开发拆成可执行、可验证、可逐步交付的 Milestone。

适用原则：

- 优先最小可运行实现
- 优先保证检索质量与 citation 可信度
- 每完成一个阶段，都要有对应测试和手工验证
- 有歧义时做合理 MVP 决策，并同步更新 README

---

## 当前状态

当前仓库已经具备第一版主链路：

- FastAPI 服务骨架已存在
- `/api/health` 可用
- `/api/knowledge/ingest` 已可导入本地 markdown
- `/api/incidents/analyze` 已可返回结构化 JSON
- 已有基础 vector retrieval + BM25 + hybrid merge
- 已有 feedback API
- 已有基础测试和离线评估脚本

因此，后续工作重点不是“从零搭建”，而是继续把检索质量、输入理解、回答可信度和评估闭环做扎实。

---

## 现在做什么

这一阶段的目标是：先把当前 MVP 从“能跑”推进到“更稳定、可调、可验证”。

### Milestone 1：检索质量加固

目标：提升 runbook 命中率，让检索结果更符合工程排障场景。

状态：已完成第一轮实现

- [x] 明确 chunk metadata 结构，补齐并统一字段命名
- [x] 增加 `doc_type`、`tags`、`service` 等可用于检索和过滤的 metadata
- [x] 优化 markdown 解析规则，处理标题前导说明、空 section、短 section
- [x] 给 ingest 增加导入统计信息，便于调试索引内容
- [x] 为 hybrid retrieval 增加更明确的 score merge 规则
- [x] 增加简单 rerank 规则，优先考虑以下信息：
  - 服务名精确命中
  - 错误码精确命中
  - 依赖名命中
  - section 标题命中
- [x] 为 retrieval 增加更多样例测试，覆盖：
  - 服务名命中
  - 错误码命中
  - dependency 命中
  - 文档类型干扰

验收标准：

- 对典型 incident 输入，top 3 结果能稳定命中正确 runbook 或 incident 文档
- retrieval 测试不只验证“有结果”，还验证“结果顺序基本合理”

---

### Milestone 2：incident 输入理解增强

目标：让 analyze 入口不只是拼接原始文本，而是真正理解 incident 输入。

状态：已完成第一轮实现

- [x] 扩展 entity extraction，至少支持：
  - `service`
  - `dependency`
  - `exception_type`
  - `error_code`
  - `keywords`
  - `symptom_tags`
- [x] 明确 query rewrite 输出结构，建议拆分为：
  - `keyword_query`
  - `semantic_query`
  - `filters`
- [x] 在检索阶段实际使用 rewrite 结果，而不是只保留一个字符串
- [x] 增加服务名、依赖名、错误码的 filter 或 boost 逻辑
- [x] 对空字符串、异常短日志、噪声日志增加更明确的输入校验和错误提示
- [x] 为 entity extraction 和 query rewrite 增加单元测试

验收标准：

- analyze 请求中的结构化中间结果可调试、可打印、可验证
- query rewrite 能明确区分“语义召回信息”和“精确命中过滤信息”

---

### Milestone 3：回答可信度增强

目标：让回答更像工程排障建议，而不是普通问答文本。

状态：已完成第一轮实现

- [x] 收紧 answer synthesis 规则，确保结论只基于召回证据
- [x] 明确区分：
  - 已有证据支持的判断
  - 可能原因
  - 不确定项
- [x] citation 增加更稳定的 excerpt 生成逻辑
- [x] 当召回结果质量不足时，返回更明确的“不确定”响应
- [x] 增加 response schema 测试，覆盖无结果、弱结果、多引用场景
- [x] 检查并统一 API response 字段命名风格

验收标准：

- 回答中不会出现脱离 citation 的关键结论
- 当知识库证据不足时，响应会明确暴露不确定性

---

## 下一步做什么

这一阶段的目标是：把“能调试、能比较、能持续优化”的闭环建起来。

### Milestone 4：评估闭环扩充

目标：让后续优化有数据依据，而不是凭感觉调 retrieval。

状态：已完成第一轮实现

- [x] 扩充 JSONL 评测集，覆盖至少 10 到 20 条典型 incident
- [x] 每条样本包含：
  - 输入
  - 期望命中文档
  - 期望关键词或异常类型
- [x] 在评测脚本中加入基础指标：
  - `hit@3`
  - `hit@5`
  - citation relevance
  - schema validity
- [x] 将评测结果输出为更稳定的结构化格式
- [x] README 增加“如何运行评测”和“如何解读指标”
- [x] 为典型失败样本建立回归用例

验收标准：

- 每次调整 retrieval 后，都可以快速比较前后效果
- 评测结果能支持判断“是 query rewrite 变差，还是 merge/rerank 变差”

---

### Milestone 5：知识库规范化

目标：让 `knowledge/` 中的文档逐步具备更稳定的 ingest 质量。

状态：已完成第一轮实现

- [x] 补一份知识文档编写规范，约束标题、tags、文档类型
- [x] 定义推荐 markdown 模板：
  - runbook
  - incident
  - service
  - faq
- [x] 明确建议 metadata 字段
- [x] 增加 ingest 前校验或 lint 脚本
- [x] 增加几份更接近真实场景的示例知识文档

验收标准：

- 新文档加入 `knowledge/` 后，ingest 结果更可预测
- metadata 和 chunk 结构足够稳定，不容易因为文档风格变化而失真

---

### Milestone 6：可调试性增强

目标：让我们在排查“为什么没召回”“为什么排错顺序”时更省时间。

状态：已完成第一轮实现

- [x] 为 ingest 增加更清晰的日志输出
- [x] 为 analyze 增加 debug 信息开关
- [x] 可选返回中间信息：
  - entities
  - rewritten queries
  - retrieval scores
  - rerank reasons
- [x] 为失败案例整理一个 debug checklist

验收标准：

- 遇到错误命中或漏召回时，可以快速定位问题在：
  - metadata
  - entity extraction
  - query rewrite
  - BM25
  - vector retrieval
  - merge/rerank

---

## 后面再做什么

这一阶段的目标是：在 MVP 稳定后，再升级底层能力和产品形态，而不是过早上复杂度。

### Milestone 7：替换或升级向量能力

状态：已完成第一轮实现

- [x] 评估是否从当前本地实现切换到 Chroma 或 FAISS
- [x] 接入真实 embedding 模型
- [x] 比较替换前后的 retrieval 指标变化
- [x] 保持存量接口不破坏现有 API

当前结论：

- 默认继续使用 `sqlite + hash embedding`
- 已接入可选 `sentence-transformers` provider
- 已提供 `scripts/compare_vector_configs.py` 对比入口
- Chroma / FAISS 暂不作为默认后端，等评测集证明有收益后再切换

适合启动的前提：

- 当前评测集已经足够覆盖主要问题场景
- 已能明确判断“问题出在 embedding 能力，而不是 query / metadata / rerank”

---

### Milestone 8：更强的 rerank 和多阶段检索

状态：已完成第一轮实现

- [x] 引入更细粒度的规则 rerank
- [x] 评估是否需要轻量 reranker
- [x] 试验分阶段检索：
  - 先按 service/doc_type 过滤
  - 再做 hybrid retrieval
  - 再做 rerank

当前结论：

- 默认继续使用规则 rerank
- 暂不引入模型 reranker
- debug 输出已包含 filter stages、score breakdown 和 rerank reasons

适合启动的前提：

- 基础 hybrid retrieval 已相对稳定
- 失败案例主要集中在排序而不是召回

---

### Milestone 9：更强的回答生成

状态：已完成首版。

已完成：

- [x] 接入可选 OpenAI answer generator 做 answer synthesis
- [x] 约束 prompt，确保答案受 citation 绑定
- [x] 增加 prompt versioning
- [x] 对比模板式回答与 LLM 回答的 usefulness

当前结论：

- 默认继续使用 template，保证离线可运行
- OpenAI 路径通过 `ANSWER_GENERATOR=openai` 启用
- debug 输出包含 answer generator、prompt version 和 usedLlm
- 离线评测新增 `answerUsefulness`
- `scripts/compare_answer_generators.py` 可比较 template/openai，缺少依赖或 API key 时会跳过 openai

决策记录：

- [ANSWER_GENERATION_DECISION.md](/Users/ironion/workspace/runbook-copilot/docs/ANSWER_GENERATION_DECISION.md)

---

### Milestone 10：产品化扩展

状态：已完成首版。

已完成：

- [x] 接入真实 incident 来源的本地留存模型
- [x] 增加通用监控/告警事件入口
- [x] 增加简单调试页面
- [x] 增加更完整的反馈闭环

当前结论：

- 先使用 `POST /api/incidents/events` 作为标准化 webhook 入口
- 已接入首个具体平台入口：`POST /api/incidents/integrations/grafana`
- analyze 和 event 入口都会写入本地 SQLite incidents 表
- feedback 支持 `useful`、`reason`、列表和汇总
- `GET /debug` 只作为本地 API demo，不作为正式前端

决策记录：

- [PRODUCTIZATION_DECISION.md](PRODUCTIZATION_DECISION.md)
- [REAL_WORLD_SAMPLE_REPLAY.md](REAL_WORLD_SAMPLE_REPLAY.md)
- [WEBHOOK_INTEGRATION_DECISION.md](WEBHOOK_INTEGRATION_DECISION.md)

---

### Milestone 11：Grafana 真实试用加固

状态：建议下一步优先启动。

目标：让 Grafana webhook 从“能接入”变成“能承接真实团队小范围试用”。

TODO：

- [ ] 基于 `sourceType + sourceId + 时间窗口` 做 webhook 去重
- [ ] 支持 Grafana `resolved` alert 更新已有 incident 状态，而不是只跳过
- [ ] 增加 incident 状态流转：
  - `analyzed`
  - `resolved`
  - `ignored`
- [ ] 抽出 Grafana 字段映射配置，至少支持 service label 候选：
  - `service`
  - `service_name`
  - `app`
  - `job`
  - `namespace`
  - `component`
- [ ] 增加真实 Grafana payload fixtures
- [ ] 增加 HMAC 签名失败、timestamp 过期、resolved alert 的测试
- [ ] README 增加 Grafana contact point 配置示例

验收标准：

- 同一个 Grafana firing alert 在短时间内不会重复生成多个 incident
- resolved alert 能把对应 incident 标记为 `resolved`
- 字段映射不需要改代码即可适配常见 label 命名
- Grafana webhook 相关测试覆盖主路径和错误路径

---

### Milestone 12：反馈驱动知识库迭代

状态：排在 Grafana 真实试用之后。

目标：让 feedback 不只是统计分数，而是能直接指导知识库补齐。

TODO：

- [ ] 增加低分 feedback 查询接口
- [ ] 增加 `useful=false` 按 `reason` 聚合接口
- [ ] 增加 incident citation 路径统计
- [ ] 增加“疑似缺知识库”报告脚本
- [ ] 支持内部脱敏告警集：
  - `app/evaluation/internal_alert_samples.jsonl`
  - 或通过参数传入自定义 dataset
- [ ] 为低分样本生成建议 runbook 文件名、tags 和章节骨架
- [ ] README 增加 feedback 驱动知识库迭代流程

验收标准：

- 可以快速列出最近低分 incident
- 可以看到低分原因聚合和缺失主题
- 可以从低分样本生成可人工审核的 runbook 草稿建议

---

### Milestone 13：第二平台接入

状态：等 Grafana 真实流量稳定后再启动。

目标：在已有通用 event schema 稳定的基础上，接入第二个最常用告警来源。

候选：

- PagerDuty webhook
- Prometheus Alertmanager 独立入口

TODO：

- [ ] 根据真实团队使用情况二选一，不同时接两个
- [ ] 抽出统一 external event adapter 接口
- [ ] 复用 `IncidentEventRequest`，避免为每个平台扩业务 schema
- [ ] 增加平台签名/鉴权策略文档
- [ ] 增加平台 payload fixtures 和端到端测试
- [ ] 明确 resolved/acknowledged 状态如何映射到 incident 状态

验收标准：

- 第二平台入口能复用 analyze、incident store、feedback 闭环
- 平台差异被限制在 adapter 层
- 不破坏 Grafana 入口和通用 `/api/incidents/events`

---

### Milestone 14：生成层增强与 LLM 默认策略

状态：等内部样本和 feedback 数据足够后再启动。

目标：判断是否值得让真实 LLM 成为某些环境的默认回答生成器。

TODO：

- [ ] 用内部真实样本对比 `template` 与 `openai`
- [ ] 增加 hallucination 回归测试
- [ ] 增加 citation 绑定失败的 fixture
- [ ] 增加 prompt version 升级策略
- [ ] 记录每次 answer generation 的 provider、model、promptVersion
- [ ] 明确哪些场景允许使用 LLM，哪些场景继续强制 template

验收标准：

- `answerUsefulness` 明显高于 template
- `citationRelevance` 和 `schemaValidity` 不下降
- 人工抽查确认没有无引用关键结论
- LLM 只作为可配置选项启用，不直接全局默认

---

## 推荐执行顺序

已完成的主线：

1. 检索质量加固
2. incident 输入理解增强
3. 回答可信度增强
4. 评估闭环扩充
5. 知识库规范化
6. 可调试性增强
7. embedding / vector store 可选升级评估
8. rerank 与多阶段检索
9. 回答生成增强
10. 产品化入口与反馈闭环

接下来建议按以下顺序推进，而不是并行摊太开：

1. Milestone 11：Grafana 真实试用加固
2. Milestone 12：反馈驱动知识库迭代
3. Milestone 13：第二平台接入
4. Milestone 14：生成层增强与 LLM 默认策略

---

## 每次开发一个任务时的标准流程

建议每个任务都按下面 5 步走：

1. 明确本次只改什么，不改什么
2. 先定义或更新 schema / 输入输出契约
3. 实现最小主路径
4. 立即补测试
5. 做一次真实 API 手工验证，并更新 README 或相关文档

---

## 最近两轮建议

如果按投入产出比排序，最建议先做的是：

### 第一轮

- [x] 扩展 entity extraction 字段
- [x] 引入 `keyword_query / semantic_query / filters`
- [x] 加 service / error_code / dependency 的 rerank 规则
- [x] 扩充 retrieval 测试

### 第二轮

- [x] 扩充评测集到 10+ 条
- [x] 加 hit@3 / hit@5
- [x] 补知识库编写规范
- [x] 增加 analyze debug 输出

这两轮做完之后，再决定是否需要引入更重的底层能力。

### 接下来两轮

### 第三轮

- [ ] webhook 去重
- [ ] resolved alert 状态更新
- [ ] Grafana 字段映射配置
- [ ] Grafana payload fixtures

### 第四轮

- [ ] 低分 feedback 列表
- [ ] useful=false reason 聚合
- [ ] 缺失知识报告脚本
- [ ] 内部脱敏告警样本支持
