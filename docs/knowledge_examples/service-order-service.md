# order-service service overview
tags: order-service, redis, postgres, service

## 服务职责
负责创建订单、更新订单状态和协调库存、支付流程。

## 核心依赖
依赖 Redis 做缓存，依赖 PostgreSQL 存储订单数据。

## 常见故障
常见问题包括 Redis 连接失败、数据库慢查询和发布后配置错误。

## 排查入口
优先查看应用错误日志、Redis 健康、数据库连接池和最近发布记录。
