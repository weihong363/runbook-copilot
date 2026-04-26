# platform-service 数据库迁移与资源争用 Runbook
tags: platform-service, database, migration, schema-drift, resource-contention, orm, runbook

## 适用场景

当事故涉及 database migration、schema drift、ORM reference removed column、resource contention on database hosts、primary database saturation、slow query、lock wait 或 schema synchronize 时，优先使用本 runbook。

## 快速判断

先确认数据库变更时间、schema 版本、ORM 映射版本、慢查询、锁等待、连接数和主库 CPU/IO 是否同时异常。

如果多个服务同时退化，优先排查共享数据库主机资源争用或控制面 schema drift。

## 处理步骤

1. 对比应用版本、ORM metadata 和数据库真实 schema。
2. 检查最近 migration 是否删除列、修改索引、改变约束或触发 schema drift。
3. 查看主库 CPU、IO、连接池、lock wait、慢查询和 replication lag。
4. 如果 ORM 仍引用已删除字段，先发布兼容代码或回滚 migration。
5. 如果是数据库主机资源争用，先限流高成本查询，必要时迁移流量或降级非核心功能。
6. 恢复后补充 backward-compatible migration、shadow query 和 schema drift preflight。

## 常见根因

- migration 先于应用兼容发布，导致 ORM 引用不存在字段。
- schema drift 导致 policy、权限或控制面更新失败。
- 新查询饱和主库，影响多个上游服务。
- 数据库主机资源争用导致错误率和延迟同时升高。

## 公开案例参考

- GitHub Availability Report: January 2025
- GitHub Availability Report: April 2025
- GitHub Availability Report: August 2025
- GitHub Availability Report: December 2025
- Cloudflare outage on November 18 2025
