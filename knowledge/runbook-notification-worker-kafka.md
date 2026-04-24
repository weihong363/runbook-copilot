# notification-worker Kafka 消费堆积 Runbook
tags: notification-worker, kafka, lag, consumer

## 适用场景
当 notification-worker 出现 Kafka consumer lag 持续升高、消息发送延迟、消费组 rebalance 频繁或批量重试时，优先参考本 runbook。

## 快速判断
检查 consumer lag、rebalance 次数、下游依赖超时和最近发布记录。

## 处理步骤
1. 查看消费组 lag、分区分配和 rebalance 日志。
2. 检查下游短信、邮件或推送依赖是否超时。
3. 核对 consumer 并发数、批量大小和重试配置。
4. 如发布后问题明显，回滚最近消费逻辑改动。

## 后续沉淀
记录 lag 峰值、受影响 topic 和处理时长。
