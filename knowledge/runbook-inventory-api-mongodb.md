# inventory-api MongoDB 连接超时 Runbook
tags: inventory-api, mongodb, timeout, connection

## 适用场景
当 inventory-api 出现 `MongoNetworkTimeout`、库存读取超时、依赖连接抖动或请求排队增加时，优先参考本 runbook。

## 快速判断
检查 MongoDB 副本集状态、网络延迟、连接池使用率和最近驱动配置变更。

## 处理步骤
1. 查看副本集主节点状态和复制延迟。
2. 检查应用到 MongoDB 的网络错误和连接池耗尽情况。
3. 核对读写超时、连接超时和驱动版本是否有变更。
4. 如发布后出现，优先回滚最近依赖配置或驱动升级。

## 后续沉淀
记录超时窗口、受影响接口和最终修复动作。
