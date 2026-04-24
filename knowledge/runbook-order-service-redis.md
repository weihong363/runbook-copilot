# order-service Redis 连接失败 Runbook
tags: order-service, redis, cache, connection

## 适用场景
当 order-service 出现 `redis connection refused`、`RedisConnectionError`、缓存连接失败或接口延迟上升时，优先参考本 runbook。

## 快速判断
检查 Redis 实例健康状态、网络连通性、连接池配置和最近配置变更。

## 处理步骤
1. 确认 Redis 实例是否存活，是否有主从切换或重启。
2. 检查应用侧 Redis 地址、端口、鉴权配置是否变更。
3. 查看连接池是否耗尽，是否存在大量重试导致的连接风暴。
4. 如果故障发生在发布后，优先回滚最近的 Redis 配置或客户端版本。

## 后续沉淀
记录连接失败的触发条件、网络影响范围和最终修复动作。
