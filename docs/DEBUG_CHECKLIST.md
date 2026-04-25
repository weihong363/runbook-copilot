# Debug Checklist

这份清单用于排查“为什么没有召回正确文档”或“为什么排序不符合预期”。

## 1. 先确认知识库是否正确入库

执行：

```bash
python ../scripts/lint_knowledge.py
python ../scripts/ingest.py
```

重点看：

- 是否所有 markdown 文件都被列出
- `indexedByDocType` 是否符合预期
- `indexedChunks` 是否明显偏少
- lint 是否提示缺少 tags、标题或 service

如果这里有问题，优先修文档格式或 `knowledge/` 路径。

## 2. 检查 metadata

重点确认：

- `doc_type` 是否正确，例如 FAQ 不应被识别成 runbook
- `service` 是否能提取出来
- `tags` 是否包含服务名、依赖名和故障主题
- section 标题是否足够具体

metadata 错误通常会影响 service filter、doc type filter 和 rerank。

## 3. 检查 entity extraction

请求 `/api/incidents/analyze` 时加入：

```json
{
  "debug": true
}
```

重点看响应中的：

- `debug.entities.dependencies`
- `debug.entities.exceptionTypes`
- `debug.entities.errorCodes`
- `debug.entities.symptomTags`

如果这里缺关键信号，问题通常在 incident 输入质量或实体抽取规则。

## 4. 检查 query rewrite

重点看：

- `debug.rewrittenQuery.keywordQuery`
- `debug.rewrittenQuery.semanticQuery`
- `debug.rewrittenQuery.filters`

判断方法：

- BM25 依赖 `keywordQuery`，错误码、服务名、依赖名应尽量出现在这里
- 向量召回依赖 `semanticQuery`，应该保留告警标题、症状和日志上下文
- `filters.service` 错误会直接影响候选文档集合

## 5. 检查 retrieval candidates

重点看：

- `debug.retrieval.totalChunks`
- `debug.retrieval.filteredChunks`
- `debug.retrieval.candidates`

如果 `filteredChunks` 远小于 `totalChunks`，先检查 service 或 doc type filter。

如果 candidates 中没有期望文档，问题更可能在 metadata、filters 或知识库内容。

## 6. 检查 score breakdown

每个 candidate 会返回：

- `vectorScore`
- `bm25Score`
- `bm25Normalized`
- `rerankBoost`
- `finalScore`
- `rerankReasons`

判断方法：

- `bm25Score` 低：关键词没有对上，先看 `keywordQuery` 和文档正文
- `vectorScore` 低：语义 query 和文档正文不够接近
- `rerankBoost` 低：service、错误码、依赖或 section 标题没有命中
- `rerankReasons` 缺少 `service_match`：检查 service metadata
- `rerankReasons` 缺少 `error_code_match`：检查错误码是否进入 filters

## 7. 常见问题定位

漏召回：

- 文档没有进 `knowledge/`
- 文件名、标题或 tags 不包含可识别 doc type
- service 没被提取出来
- query rewrite 缺少关键错误码或依赖名

排序错误：

- 期望文档进了 candidates，但 `finalScore` 不高
- `bm25Normalized` 高但 `rerankBoost` 低
- 标题 chunk 抢分，需要检查 section 标题和正文

弱证据回答：

- citations 存在但分数低
- 命中的 section 不是具体排障步骤
- 当前知识库只有相邻场景，没有该服务的直接 runbook
