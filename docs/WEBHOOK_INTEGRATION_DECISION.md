# Webhook Integration Decision

本轮把公开真实告警样本从 26 条扩展到 40 条，继续验证 `IncidentEventRequest` 是否足够稳定。

## Schema 稳定性结论

当前事件 schema 暂不需要扩字段：

- `sourceType` 能区分 `public-postmortem`、`public-status-page`、`grafana-webhook`
- `sourceId` 能承接外部告警 fingerprint / group key
- `alertTitle`、`serviceName`、`logSnippet`、`symptomDescription` 足够支撑当前 RAG 分析
- `severity` 和 `labels` 足够承接平台元数据

样本覆盖增加后，主要缺口仍然来自知识库，而不是事件 schema。

## 首个接入平台

优先接入 Grafana Alerting webhook。

原因：

- Grafana contact point 官方支持 Webhook。
- Grafana webhook 支持 HMAC-SHA256 签名，适合最小安全校验。
- Grafana / Alertmanager payload 天然包含 `alerts`、`labels`、`annotations`、`fingerprint`，容易映射到当前事件 schema。
- 对工程团队来说，Grafana / Prometheus 告警是最常见的告警来源之一。

## 已实现入口

```text
POST /api/incidents/integrations/grafana
```

当前行为：

- 接收 Grafana/Alertmanager 风格 JSON payload
- 跳过 `resolved` alert
- 每条 firing alert 转成 `IncidentEventRequest`
- 复用 `/api/incidents/events` 的分析和落库流程
- 返回生成的 `incidentIds`

## 字段映射

| Grafana 字段 | Runbook Copilot 字段 |
| --- | --- |
| `labels.service` / `labels.job` / `labels.app` | `serviceName` |
| `labels.alertname` | `alertTitle` 的主要告警名 |
| `annotations.description` / `annotations.message` | `logSnippet` |
| `annotations.summary` | `symptomDescription` |
| `labels.severity` / `labels.priority` | `severity` |
| `fingerprint` / `groupKey` | `sourceId` |
| labels 合并结果 | `labels` |

## 签名校验

如果配置了：

```env
GRAFANA_WEBHOOK_SECRET=...
```

接口会校验 Grafana HMAC 签名：

- 默认签名 header：`X-Grafana-Alerting-Signature`
- 可选 timestamp header：`X-Grafana-Alerting-Signature-Timestamp`
- timestamp 最大允许偏移：300 秒

如果未配置 secret，接口仍可用于本地调试和内网 PoC。

## 下一步

暂不接 PagerDuty / Prometheus Alertmanager 独立入口。优先观察 Grafana webhook 真实请求中的字段差异，再决定是否需要：

- 自定义 service 字段映射配置
- webhook 去重窗口
- resolved 事件状态更新
- 更严格的签名配置和 replay 防护
