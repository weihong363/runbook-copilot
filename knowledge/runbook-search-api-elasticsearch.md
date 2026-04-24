# search-api Elasticsearch 查询超时 Runbook
tags: search-api, elasticsearch, timeout, query

## 适用场景
当 search-api 出现 `ElasticsearchTimeoutError`、搜索查询超时、响应延迟明显上升或请求堆积时，优先使用本 runbook。

## 快速判断
检查 Elasticsearch 集群健康、线程池队列、热点索引和最近查询模板变更。

## 处理步骤
1. 查看集群 health、节点负载和线程池拒绝数。
2. 检查慢查询日志，确认是否有高基数聚合或无界查询。
3. 核对最近发布的查询模板、索引映射和分片配置。
4. 必要时降级高成本搜索功能或缩小查询范围。

## 后续沉淀
记录热点索引、慢查询样本和最终优化动作。
