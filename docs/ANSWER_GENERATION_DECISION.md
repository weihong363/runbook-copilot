# Answer Generation Decision

Milestone 9 的结论：当前默认继续使用模板生成，但已经接入可选 OpenAI answer generator，并通过 prompt version、schema 校验和 citation 绑定约束生成结果。

## 当前决策

默认配置：

```env
ANSWER_GENERATOR=template
ANSWER_PROMPT_VERSION=grounded-v1
OPENAI_MODEL=gpt-5.2
```

原因：

- MVP 必须保证离线可运行，模板生成没有外部依赖
- 当前检索和 citation 质量仍然是答案可信度的基础
- 真实 LLM 可以提升表达和步骤组织，但不能替代 grounded retrieval

## 已完成的升级点

- 回答生成层已从 incident analyzer 中拆出
- 新增 `AnswerGenerator` 协议，支持模板和 OpenAI 两种实现
- 新增 `grounded-v1` prompt version
- OpenAI 路径使用结构化 JSON schema 输出
- LLM 输出后会再次执行 citation binding，只允许引用本次检索结果中的 chunk
- debug 输出包含 answer generator、prompt version 和是否使用 LLM
- 离线评测新增 `answerUsefulness`
- 新增 `scripts/compare_answer_generators.py` 对比模板和 LLM 路径

## Citation 约束

生成层必须遵守：

- `citations` 只能来自检索结果
- 如果 LLM 返回了不存在的 `chunkId`，系统会丢弃该引用
- 如果 LLM 没有返回有效引用，系统会回退到检索结果前 3 条 citation
- 没有检索结果时，不调用 LLM，直接返回知识库不足说明

## 如何试验 LLM

安装可选依赖：

```bash
pip install -r requirements-llm.txt
```

运行单次评测：

```bash
ANSWER_GENERATOR=openai OPENAI_MODEL=gpt-5.2 python -m app.evaluation.evaluate
```

比较生成器：

```bash
python scripts/compare_answer_generators.py
```

如果本地没有安装 `openai` 或缺少 API key，OpenAI 路径会被标记为 `skipped`。

## 何时切换默认生成器

满足以下条件后再考虑把默认值从 `template` 改为 `openai`：

- 评测集扩展到更真实的 30 到 50 条样本
- `answerUsefulness` 明显高于模板路径
- `citationRelevance` 和 `schemaValidity` 不下降
- 人工抽查确认 LLM 没有引入无引用关键结论

## 后续建议

- 扩展 prompt version，比如 `grounded-v2`
- 增加针对 LLM 输出的 hallucination fixture
- 将人工反馈和离线评测结果关联起来
- 记录每次生成的 prompt version，便于后续排查回归
