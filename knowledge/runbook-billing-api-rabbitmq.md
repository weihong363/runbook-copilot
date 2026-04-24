# billing-api RabbitMQ 连接中断 Runbook
tags: billing-api, rabbitmq, connection, queue

## 适用场景
当 billing-api 出现 `connection reset by peer`、RabbitMQ 连接中断、账单任务积压或发布后消息发送失败时，优先参考本 runbook。

## 快速判断
检查 RabbitMQ 节点健康、连接数、队列堆积和最近证书或网络变更。

## 处理步骤
1. 查看 RabbitMQ 节点状态和队列积压情况。
2. 检查应用侧连接是否频繁重建，是否有证书或鉴权错误。
3. 核对网络层是否存在连接 reset 或中断。
4. 如发布后问题出现，优先回滚消息客户端或连接配置改动。

## 后续沉淀
记录队列积压时长、连接错误码和修复动作。
