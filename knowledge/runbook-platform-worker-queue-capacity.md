# platform-service Worker 队列容量 Runbook
tags: platform-service, worker, queue, capacity, backlog, runbook

## 适用场景

当后台 worker、通知投递、异步任务、代码扫描、事件处理、Kafka pipeline、data pipeline 或 review pipeline 出现 queue backlog、run start delay、job failure、delivery latency、worker pools close to capacity、backpressure、SLO miss、rate limit、throttle、backoff、misconfiguration、monitoring gap 时，优先使用本 runbook。

## 快速判断

先确认 backlog 增长速度、队列最老消息等待时间、worker 可用实例数、处理吞吐、失败率和最近流量峰值。

如果用户侧表现为通知延迟、任务启动延迟、异步 review 失败、事件投递延迟或页面数据缺失，通常需要同时看队列堆积、Kafka topic / pipeline 发布状态和下游依赖延迟。

## 处理步骤

1. 查看 queue depth、oldest message age、worker utilization 和 per-stage latency。
2. 检查 worker pool 是否接近容量上限，是否有批量任务或流量峰值。
3. 检查下游依赖是否 timeout 或 elevated response time，避免只扩 worker 放大下游压力。
4. 临时扩大 worker capacity 或降低任务启动速率，优先保护关键路径。
5. 如果是 Kafka pipeline misconfiguration，先确认数据是否发布到正确 topic，并检查 consumer lag 和 monitoring。
6. 如果命中外部 rate limit，降低启动速率，增加 backoff，避免重试风暴。
7. 对积压任务分优先级，先恢复用户可见路径，再处理低优先级 backlog。
8. 恢复后提高 baseline capacity，并补充容量预警、SLO burn rate、pipeline monitoring 和负载预测。

## 常见根因

- worker pool 运行过于接近容量上限。
- 下游依赖延迟升高导致 request timeout 和 backpressure。
- 队列消费速率低于生产速率，持续 backlog。
- 关键路径上存在 throttling 或 rate limit。
- 缺少 backoff，导致被限流后持续放大排队。

## 公开案例参考

- GitHub Availability Report: February 2025
- GitHub Availability Report: June 2025
- GitHub Availability Report: December 2025
- AWS Service Event US-EAST-1 June 2023
