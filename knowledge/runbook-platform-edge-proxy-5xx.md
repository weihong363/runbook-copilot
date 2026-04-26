# platform-service 边缘代理与 WAF 5xx Runbook
tags: platform-service, edge, proxy, waf, cdn, 5xx, turnstile, workers-kv, runbook

## 适用场景

当 CDN、edge proxy、WAF、bot management、Workers KV、Access、Turnstile、Email Security、IP reputation source、Git control plane、raw file access、search endpoints 或 dashboard login 出现 HTTP 500、HTTP 5xx spike、failed to load、authentication failures、proxy panic、nil value、configuration file、traffic spike、search traffic spike、request timeout、limit、detection accuracy reduced 异常时，优先使用本 runbook。

## 快速判断

先确认 5xx 是否来自源站还是边缘代理。如果多个下游产品同时失败，并且错误集中在 proxy/WAF/Access/KV 前端，优先按边缘代理共享依赖排查。若只有未登录流量、搜索端点或 API request timeout 升高，优先按 traffic spike / search / limit 方向排查。

## 处理步骤

1. 按产品、colo、rule、feature flag、proxy version 分组查看 5xx。
2. 检查最近 WAF 规则、bot feature file、global configuration、ClickHouse 查询或安全缓解变更。
3. 如果错误来自 proxy module panic 或 nil value，优先启用 kill switch 或回滚到 last-known-good 配置文件。
4. 如果是 unauthenticated search traffic spike，先按 search endpoints 限流并启用 automated traffic management。
5. 检查 Workers KV、Access、Turnstile、Email Security、Git SSH/HTTP operations 是否因为 core proxy 或 control plane 失败产生连锁影响。
6. 如果 temporary loss of IP reputation source，先降级依赖该 source 的检测规则，避免误判，并标注检测准确性下降。
7. 如 observability/debug 系统放大 CPU 或延迟，临时降级错误增强逻辑。
8. 恢复后补充配置文件校验、强类型重写、全局配置灰度、reputation source 健康检查和模块级 fail-open/fail-small 机制。

## 常见根因

- 配置文件大小或结构超出模块假设。
- 全局配置秒级传播，缺少逐步 rollout。
- WAF rule skipped 后代码仍访问不存在对象，触发 nil value。
- Bot Management 或 proxy 模块 panic 导致 HTTP 5xx。
- 下游产品依赖 core proxy，出现 Access 登录失败、Workers KV 5xx 或 Turnstile failed to load。
- traffic spike primarily to search endpoints 导致 slow page load、API request timeout 或 Git control plane 压力。
- Email Security temporary loss of access to IP reputation source，导致 spam detection accuracy reduced。

## 公开案例参考

- Cloudflare outage on November 18 2025
- Cloudflare outage on December 5 2025
