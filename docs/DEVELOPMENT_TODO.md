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

TODO：

- [ ] 引入更细粒度的规则 rerank
- [ ] 评估是否需要轻量 reranker
- [ ] 试验分阶段检索：
  - 先按 service/doc_type 过滤
  - 再做 hybrid retrieval
  - 再做 rerank

适合启动的前提：

- 基础 hybrid retrieval 已相对稳定
- 失败案例主要集中在排序而不是召回

---

### Milestone 9：更强的回答生成

TODO：

- [ ] 接入真实 LLM 做 answer synthesis
- [ ] 约束 prompt，确保答案受 citation 绑定
- [ ] 增加 prompt versioning
- [ ] 对比模板式回答与 LLM 回答的 usefulness

适合启动的前提：

- citation 和 retrieval 质量已足够稳定
- 能明确验证生成层带来的收益，而不是掩盖检索问题

---

### Milestone 10：产品化扩展

TODO：

- [ ] 接入真实 incident 来源
- [ ] 接入监控平台或告警事件源
- [ ] 增加简单前端或调试页面
- [ ] 增加更完整的反馈闭环

注意：

- 这些都不应该早于 retrieval 和评估闭环稳定完成

---

## 推荐执行顺序

建议按以下顺序推进，而不是并行摊太开：

1. 检索质量加固
2. incident 输入理解增强
3. 回答可信度增强
4. 评估闭环扩充
5. 知识库规范化
6. 可调试性增强
7. 再决定是否升级 embedding / vector store / reranker / LLM

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

- [ ] 扩展 entity extraction 字段
- [ ] 引入 `keyword_query / semantic_query / filters`
- [ ] 加 service / error_code / dependency 的 rerank 规则
- [ ] 扩充 retrieval 测试

### 第二轮

- [ ] 扩充评测集到 10+ 条
- [ ] 加 hit@3 / hit@5
- [ ] 补知识库编写规范
- [ ] 增加 analyze debug 输出

这两轮做完之后，再决定是否需要引入更重的底层能力。
