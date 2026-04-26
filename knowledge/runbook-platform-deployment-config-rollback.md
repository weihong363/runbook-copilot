# platform-service 配置变更与部署回滚 Runbook
tags: platform-service, deployment, configuration, feature-flag, rollback, dependency, runbook

## 适用场景

当告警包含 deployment、configuration change、manual configuration、internal dependency、create start failures、feature flag、missing Docker image、CORS error、global configuration、safe rollout、rate limiter invalid state 等信号时，优先使用本 runbook。

## 快速判断

先核对事故开始时间与最近部署、配置发布、feature flag 变更、依赖镜像或客户端请求头变更是否重合。

如果症状在回滚 feature flag、恢复旧配置或补齐依赖镜像后快速缓解，应把变更链路作为首要方向。

## 处理步骤

1. 查询最近 2 小时内的部署、配置变更、feature flag rollout 和依赖版本变更。
2. 确认变更是否经过灰度；如果是 global configuration，优先评估全局回滚或 kill switch。
3. 对缺失依赖如 Docker image、模型配置、WAF 规则、客户端 header，检查发布校验是否覆盖。
4. 如果用户影响持续扩大，先回滚到 last-known-good 配置。
5. 恢复后补充 pre-deployment validation、配置 diff 检查、safe rollout 和逐步 rollout。

## 常见根因

- 配置变更未走灰度，数秒内传播到全量环境。
- manual configuration changes to internal dependency 导致 create/start failures。
- feature flag 组合进入无效状态，触发 403、500 或请求失败。
- 部署组件引用了缺失镜像或未验证的关键依赖。
- 客户端请求头或 CORS 策略变更未覆盖真实上传路径。

## 公开案例参考

- GitHub Availability Report: February 2025
- GitHub Availability Report: April 2025
- GitHub Availability Report: May 2025
- GitHub Availability Report: September 2025
- Cloudflare outage on December 5 2025
