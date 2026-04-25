# Vector Backend Decision

Milestone 7 的结论：当前默认继续使用 `sqlite + hash embedding`，但代码已经拆成可替换的 embedding provider 和 vector store factory。

## 当前决策

默认配置：

```env
VECTOR_STORE_BACKEND=sqlite
EMBEDDING_PROVIDER=hash
VECTOR_DIMENSION=128
```

原因：

- 当前 10 条离线评测集已经达到 `hitAt3=1.0`、`hitAt5=1.0`、`citationRelevance=1.0`
- 当前主要风险不在向量库能力，而在知识库覆盖、query rewrite 和 rerank 规则
- Chroma / FAISS 会增加安装和运行复杂度，暂时没有被评测数据证明是必要的

## 已完成的升级点

- embedding provider 已抽象，可在不改 API 的情况下切换
- vector store 已通过 factory 创建，后续可挂 Chroma / FAISS
- 默认实现仍然离线可运行
- 提供了配置对比脚本

## 可选真实 embedding

如果本地安装了 `sentence-transformers`，可以试验：

```bash
EMBEDDING_PROVIDER=sentence-transformers \
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
python -m app.evaluation.evaluate
```

如果未安装依赖，系统会给出明确错误，不影响默认路径。

## 配置对比

```bash
python scripts/compare_vector_configs.py
```

该脚本默认比较：

- `hash`
- `sentence-transformers`

未安装的 provider 会被标记为 `skipped`，已可用 provider 会输出评测 summary。

## 何时再切换 Chroma / FAISS

满足以下条件时再切换更合适：

- 评测集扩展到更真实的 30 到 50 条样本
- 出现明确的语义召回失败，而不是 metadata / filter / rerank 问题
- `hitAt5` 下降但 `keywordCoverage` 和 rerank 规则正常
- 本地数据量增长到 SQLite 全量扫描明显影响响应时间

下一轮升级建议：

- 保持 `VectorStore` 接口不变
- 增加 `ChromaVectorStore` 或 `FaissVectorStore`
- 用 `scripts/compare_vector_configs.py` 比较指标
- 指标稳定后再把默认 backend 从 `sqlite` 改掉
