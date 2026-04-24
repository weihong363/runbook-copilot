# user-service MySQL 死锁排障 Runbook
tags: user-service, mysql, deadlock, transaction

## 适用场景
当 user-service 出现 `Deadlock found when trying to get lock`、事务重试增多或用户更新接口失败时，优先参考本 runbook。

## 快速判断
检查死锁日志、热点表更新路径、事务持续时间和最近发布改动。

## 处理步骤
1. 查看 MySQL 死锁日志和最近的冲突 SQL。
2. 检查是否存在跨表更新顺序不一致。
3. 缩短事务范围，确认是否引入了额外锁等待。
4. 如果新版本引入批量更新逻辑，优先回滚该改动。

## 后续沉淀
记录冲突 SQL、表级热点和修复方案。
