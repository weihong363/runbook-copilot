# Productization Decision

Milestone 10 的结论：当前先补齐最小产品闭环，不接具体外部平台 SDK。

## 当前决策

已实现：

- 通用告警事件入口：`POST /api/incidents/events`
- incident 本地留存：`GET /api/incidents`、`GET /api/incidents/{incidentId}`
- feedback 扩展：`useful`、`reason`、列表和汇总接口
- 极简本地调试页：`GET /debug`

暂不实现：

- Grafana / Prometheus / PagerDuty 的真实 SDK 集成
- 认证、RBAC、多租户
- 后台 worker
- 正式前端应用

原因：

- MVP 当前最需要的是可验证的闭环，而不是平台绑定
- 通用事件 schema 已足够让脚本、webhook 或人工工具调用
- 外部平台集成会带来认证、签名校验、重试和权限边界，应该在 API 契约稳定后再做

## Incident 入口约定

`POST /api/incidents/events` 接收标准化事件：

- `sourceType`：来源类型，例如 `grafana-webhook`
- `sourceId`：来源系统里的事件 ID
- `alertTitle`
- `serviceName`
- `logSnippet`
- `symptomDescription`
- `severity`
- `labels`

该接口会复用 `/api/incidents/analyze` 的分析流程，并把分析结果写入 SQLite。

## Feedback 闭环

反馈接口新增：

- `useful`：用户是否认为答案有用
- `reason`：简短原因标签
- `GET /api/feedback`
- `GET /api/feedback/summary`

后续可以把 feedback 与离线评测结合，用真实用户反馈挑选需要补知识库或调 rerank 的案例。

## 调试页边界

`GET /debug` 是本地 API demo，不是正式前端。

它只做：

- 输入告警标题、服务名、日志和症状
- 调用 `/api/incidents/analyze`
- 展示原始 JSON 响应

它不做：

- 登录
- 历史管理
- 图表
- 复杂交互

## 下一步建议

优先顺序：

1. 用真实团队的 20 到 30 条告警样本调用 `/api/incidents/events`
2. 观察 feedback summary 中低评分和 `useful=false` 的案例
3. 将缺失知识沉淀到 `knowledge/`
4. 再决定是否接具体告警平台 webhook 签名和字段映射
