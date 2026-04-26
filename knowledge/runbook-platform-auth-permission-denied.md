# platform-service 鉴权 Permission Denied Runbook
tags: platform-service, auth, permission-denied, jwt, sts, saml, rate-limit, runbook

## 适用场景

当请求出现 permission denied、403、PERMISSION_DENIED、publish/subscribe denied、JWT could not be verified、SAML federation errors、STS throttles、authentication failures、login blocked、expired credentials、double opt-in failed、existing sessions unaffected、configuration rollback 等信号时，优先使用本 runbook。

## 快速判断

先区分是鉴权失败、限流、token 校验、权限规则还是登录依赖故障。已有会话正常但新登录失败，通常指向 token、STS、SAML、captcha 或登录链路依赖。

## 处理步骤

1. 检查 401/403/PERMISSION_DENIED 错误比例，并按区域、租户、客户端类型分组。
2. 对比 JWT key rotation、配置 rollout、SAML/OIDC/STS 依赖、credential expiry 和权限规则变更。
3. 确认 existing sessions 是否正常；如果正常，优先排查新 token 签发和验证链路。
4. 检查 rate limiter 是否进入 invalid state，是否把 100% 请求限流。
5. 如由 configuration mismatch 或 bad configuration change 导致，优先 rollback 或加速 rollout 让配置重新一致。
6. 如果是 expired credentials，先轮换凭证并验证依赖服务调用，再补充到期前告警。
7. 恢复后补充 token/key rotation 验证、跨区域配置一致性检查和登录链路探针。

## 常见根因

- JWT key rotation 或配置时间戳 mismatch。
- Firebase rules / IAM / policy 配置不一致。
- Pub/Sub publish 和 subscribe API 因 bad configuration change 返回 permission denied。
- STS throttling 导致 SAML federation 新登录失败。
- internal service expired credentials 导致 unsubscribe、double opt-in 或登录依赖失败。
- 全局 rate limiter 配置错误导致 403。
- 登录页依赖的 captcha 或 access proxy 不可用。

## 公开案例参考

- Google Cloud Service Health: Cloud Pub/Sub April 2024
- Google Cloud Service Health: Cloud Firestore November 2023
- AWS Service Event US-EAST-1 June 2023
- GitHub Availability Report: September 2025
- Cloudflare outage on November 18 2025
