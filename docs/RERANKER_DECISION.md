# Reranker Decision

Milestone 8 的结论：当前继续使用规则 rerank，不引入额外模型 reranker。

## 当前实现

检索流程已经拆成三阶段：

1. 按 metadata 做候选过滤
2. 对候选执行 BM25 + vector hybrid retrieval
3. 使用规则 rerank 排序

当前 rerank 会考虑：

- service 精确命中
- error code 命中
- dependency 命中
- tags 命中
- doc type 是否符合请求
- section 标题命中
- query phrase 是否出现在 chunk 文本中
- title chunk 惩罚
- runbook 文档轻微加权

这些原因会在 `debug.retrieval.candidates[].rerankReasons` 中返回。

## 为什么暂不引入模型 reranker

当前离线评测集结果仍然稳定：

- `hitAt3=1.0`
- `hitAt5=1.0`
- `citationRelevance=1.0`

因此现阶段排序问题还没有足够证据证明需要引入额外模型。模型 reranker 会增加依赖、延迟和调试复杂度，暂时不符合 MVP 的简单性原则。

## 何时再引入轻量 reranker

出现以下情况时再考虑：

- `hitAt5` 正常但 `citationRelevance` 持续下降
- 期望文档进入候选集，但规则 rerank 排序失败
- `rerankReasons` 显示规则命中充分，但 final score 仍不符合人工判断
- 评测集扩大后，排序失败集中在语义相近文档之间

## 后续接入建议

优先保持接口不变：

- `HybridRetriever.searchWithDebug`
- `RetrievalDebug`
- `RetrievalDebugItem`

新增模型 reranker 时，建议作为最终阶段插入：

```text
metadata filter -> hybrid retrieval -> rule rerank -> model rerank
```

模型 rerank 的分数也应该进入 debug 输出，避免排序变成黑箱。
