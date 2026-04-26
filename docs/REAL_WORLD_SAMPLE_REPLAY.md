# Real World Alert Replay

本轮使用公开事故复盘和状态页整理了 40 条告警样本，用来验证 `/api/incidents/events` 的产品化入口和知识库覆盖情况。

## 样本来源

样本来自以下公开来源：

- GitHub Availability Reports 2025
- Google Cloud Service Health incident reports
- AWS Service Event summaries
- Cloudflare outage postmortems

样本文件：

- [real_world_alert_samples.jsonl](../app/evaluation/real_world_alert_samples.jsonl)

回放脚本：

- [run_real_world_alert_samples.py](../scripts/run_real_world_alert_samples.py)

## 回放方式

启动 API 后先导入知识库：

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/ingest
```

执行公开样本回放：

```bash
python scripts/run_real_world_alert_samples.py --post-feedback
```

脚本会逐条调用：

- `POST /api/incidents/events`
- `POST /api/feedback`

评分规则是轻量启发式：如果回答和 citation 覆盖样本预期主题词，则标记为 `useful=true`；否则标记为 `useful=false`，用于发现知识缺口。

## 观察结果

初始知识库只覆盖内部示例服务时：

- total: 26
- useful: 5
- notUseful: 21

主要缺口：

- worker / queue capacity / backlog
- deployment / configuration rollback
- database migration / schema drift / resource contention
- auth / permission denied / STS / SAML
- serverless / EventBridge / API Gateway / Fargate control plane
- edge proxy / WAF / CDN / 5xx
- Git control plane

补充通用 runbook 后：

- total: 26
- useful: 26
- notUseful: 0

继续扩充到 40 条公开样本后：

- total: 40
- useful: 40
- notUseful: 0
- schema: 暂不需要新增字段
- 首个建议接入平台：Grafana Alerting webhook

## 本轮新增知识

- [runbook-platform-worker-queue-capacity.md](../knowledge/runbook-platform-worker-queue-capacity.md)
- [runbook-platform-deployment-config-rollback.md](../knowledge/runbook-platform-deployment-config-rollback.md)
- [runbook-platform-database-schema-contention.md](../knowledge/runbook-platform-database-schema-contention.md)
- [runbook-platform-auth-permission-denied.md](../knowledge/runbook-platform-auth-permission-denied.md)
- [runbook-platform-serverless-control-plane.md](../knowledge/runbook-platform-serverless-control-plane.md)
- [runbook-platform-edge-proxy-5xx.md](../knowledge/runbook-platform-edge-proxy-5xx.md)
- [runbook-platform-git-control-plane.md](../knowledge/runbook-platform-git-control-plane.md)

## 是否接具体 webhook

当前已经接入 Grafana Alerting webhook 作为首个具体平台。

理由：

- 通用 `/api/incidents/events` 已能承接公开事故样本，schema 暂时稳定。
- Grafana / Alertmanager payload 与当前 schema 贴合，适合作为首个薄适配层。
- 签名校验通过 `GRAFANA_WEBHOOK_SECRET` 可选启用。

建议下一步先做：

1. 用团队内部真实告警继续扩充 `real_world_alert_samples.jsonl`。
2. 将 `useful=false` 的样本沉淀为 runbook。
3. 观察 Grafana webhook 真实 payload 中 service/summary/description 字段是否稳定。
4. 再决定是否接 PagerDuty 或独立 Alertmanager 入口。
