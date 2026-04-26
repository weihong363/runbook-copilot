import hashlib
import hmac
import time

from app.models.schemas import GrafanaAlert, GrafanaWebhookPayload, IncidentEventRequest

SIGNATURE_HEADER = "x-grafana-alerting-signature"
TIMESTAMP_HEADER = "x-grafana-alerting-signature-timestamp"
MAX_SIGNATURE_AGE_SECONDS = 300


def verifyGrafanaSignature(rawBody: bytes, headers: dict[str, str], secret: str | None) -> None:
    if not secret:
        return
    signature = headers.get(SIGNATURE_HEADER)
    if not signature:
        raise ValueError("缺少 Grafana webhook 签名")
    timestamp = headers.get(TIMESTAMP_HEADER)
    signedBody = rawBody
    if timestamp:
        _validateTimestamp(timestamp)
        signedBody = f"{timestamp}:".encode("utf-8") + rawBody
    expected = hmac.new(secret.encode("utf-8"), signedBody, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Grafana webhook 签名无效")


def grafanaPayloadToEvents(payload: GrafanaWebhookPayload) -> list[IncidentEventRequest]:
    alerts = payload.alerts or [_singleAlertFromPayload(payload)]
    return [_alertToEvent(payload, alert) for alert in alerts if alert.status.lower() != "resolved"]


def countResolvedAlerts(payload: GrafanaWebhookPayload) -> int:
    return sum(1 for alert in payload.alerts if alert.status.lower() == "resolved")


def _alertToEvent(payload: GrafanaWebhookPayload, alert: GrafanaAlert) -> IncidentEventRequest:
    labels = {**payload.commonLabels, **payload.groupLabels, **alert.labels}
    annotations = {**payload.commonAnnotations, **alert.annotations}
    alertName = _firstValue(labels, ["alertname", "alert", "rule"]) or payload.title or "grafana alert"
    service = _firstValue(labels, ["service", "service_name", "app", "job", "namespace"]) or "unknown-service"
    severity = _firstValue(labels, ["severity", "priority"]) or _statusToSeverity(alert.status)
    description = _firstValue(annotations, ["description", "message", "summary"]) or payload.message or alertName
    sourceId = alert.fingerprint or payload.groupKey
    return IncidentEventRequest(
        sourceType="grafana-webhook",
        sourceId=sourceId,
        alertTitle=f"{service} {alertName}",
        serviceName=service,
        logSnippet=description,
        symptomDescription=annotations.get("summary"),
        severity=severity,
        labels={key: str(value) for key, value in labels.items()},
    )


def _singleAlertFromPayload(payload: GrafanaWebhookPayload) -> GrafanaAlert:
    return GrafanaAlert(
        status=payload.status,
        labels={**payload.commonLabels, **payload.groupLabels},
        annotations=payload.commonAnnotations,
        fingerprint=payload.groupKey,
    )


def _firstValue(values: dict[str, str], names: list[str]) -> str | None:
    for name in names:
        value = values.get(name)
        if value:
            return str(value)
    return None


def _statusToSeverity(status: str) -> str:
    return "resolved" if status.lower() == "resolved" else "warning"


def _validateTimestamp(timestamp: str) -> None:
    try:
        value = int(timestamp)
    except ValueError as error:
        raise ValueError("Grafana webhook timestamp 无效") from error
    if abs(int(time.time()) - value) > MAX_SIGNATURE_AGE_SECONDS:
        raise ValueError("Grafana webhook timestamp 已过期")
