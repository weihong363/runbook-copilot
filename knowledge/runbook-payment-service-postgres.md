# payment-service PostgreSQL 连接耗尽 Runbook
tags: payment-service, postgres, database, pool

## 适用场景
当 payment-service 出现 `remaining connection slots are reserved`、连接池耗尽、下单失败率升高或发布后 5xx 上升时，优先参考本 runbook。

## 快速判断
检查 PostgreSQL 活跃连接数、长事务、慢查询和应用连接池上限。

## 处理步骤
1. 查看数据库当前活跃 session 和空闲事务。
2. 检查是否有长事务或慢查询持续占用连接。
3. 核对应用连接池上限、超时和重试参数。
4. 如果问题发生在发布后，优先回滚最近改动或降低流量。

## 后续沉淀
记录峰值连接数、慢查询样本和长期容量修复计划。
