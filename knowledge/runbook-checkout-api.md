# checkout-api 5xx 排障 Runbook
tags: checkout-api, 5xx, database, pool

## 适用场景
当 checkout-api 出现 HTTP 500、DB_POOL_EXHAUSTED、数据库连接获取超时或下单失败率升高时，优先使用本 runbook。

## 快速判断
检查最近 15 分钟错误率、数据库连接池使用率、慢查询数量和最近发布记录。

## 处理步骤
1. 查看应用日志中是否出现 DB_POOL_EXHAUSTED 或 timeout acquiring connection。
2. 检查数据库连接池上限、活跃连接数和等待队列。
3. 如果刚发布过新版本，优先回滚或降低流量。
4. 对慢查询进行采样，确认是否有订单表或库存表锁等待。

## 后续沉淀
事故结束后记录触发条件、临时缓解动作、最终根因和长期修复计划。
