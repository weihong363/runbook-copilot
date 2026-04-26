# platform-service Serverless 与控制面 Runbook
tags: platform-service, lambda, eventbridge, apigateway, fargate, control-plane, insufficient-capacity, runbook

## 适用场景

当 Lambda invocation、EventBridge delivery latency、API Gateway errors、Fargate Insufficient Capacity、container control plane、internal network unavailable、infrastructure recovery、component taken out of service、provisioning new resources、console unavailable、504 Time-out、error rate 或 provisioning latency 升高时，优先使用本 runbook。

## 快速判断

先区分数据面是否仍可服务，以及控制面是否无法创建、启动、投递、登录 console 或扩容。已有资源正常但新资源创建失败，通常指向 control plane 或 capacity pool。若用户看到 console unavailable 或 504 timeout，优先查看控制面依赖和区域性错误率。

## 处理步骤

1. 检查 invocation error rate、p95 latency、delivery latency、provisioning latency 和 throttle。
2. 区分现有任务/函数是否正常，新建、扩容、投递或登录是否失败。
3. 检查上游控制面依赖，如 internal network、EC2 control plane、STS、Lambda frontend。
4. 对 backlog 场景，先降低新请求速率，保护已有 workload。
5. 对 Insufficient Capacity，按实例规格、区域和容量池分组，尝试切换规格或区域。
6. 如果组件被错误下线且无法恢复，优先 provision new resources，验证新资源可处理真实流量后再切换。
7. 恢复后补充 cell size 上限、容量池预警、控制面依赖隔离、infrastructure recovery runbook 和 backlog drain 预案。

## 常见根因

- Lambda frontend 扩容触发 latent defect。
- EventBridge 投递到 Lambda 的链路堆积，delivery latency 升高。
- API Gateway 因内部网络不可用进入需要回收替换的坏状态。
- Fargate 控制面恢复后仍因 backlog 出现 Insufficient Capacity。
- 控制面 API 错误影响新资源创建，但已有运行实例仍正常。
- routine internal improvements 中组件被 improperly taken out of service，导致只能通过重新 provision 资源恢复。

## 公开案例参考

- AWS Service Event US-EAST-1 June 2023
- AWS Service Event US-EAST-1 December 2021
