# auth-service FAQ
tags: auth-service, faq, token, auth

## Token 过期导致 401
如果 auth-service 在短时间内出现大量 401，先确认 token 过期时间、签名密钥是否发生轮换，以及网关是否缓存了旧配置。

## 发布后登录失败
如果发布后登录失败率上升，优先检查回调地址、密钥配置和会话存储连通性。
