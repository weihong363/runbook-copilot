# profile-service ClickHouse 查询变慢 Runbook
tags: profile-service, clickhouse, latency, query

## 适用场景
当 profile-service 出现 ClickHouse 查询延迟升高、分析接口超时或慢查询集中增加时，优先使用本 runbook。

## 快速判断
检查 ClickHouse 查询队列、热点表、最近 SQL 模板变更和资源使用情况。

## 处理步骤
1. 查看慢查询日志和最耗时 SQL 模板。
2. 检查是否有大范围扫描、无谓排序或聚合放大。
3. 核对最近发布是否修改查询字段、过滤条件或分区策略。
4. 必要时先降级高成本分析接口。

## 后续沉淀
记录慢查询样本、热点表和优化措施。
