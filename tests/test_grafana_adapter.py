import hashlib
import hmac
import time

import pytest

from app.models.schemas import GrafanaWebhookPayload
from app.services.grafana_adapter import grafanaPayloadToEvents, verifyGrafanaSignature


def testGrafanaPayloadToEventsUsesCommonLabelsAndAnnotations() -> None:
    payload = GrafanaWebhookPayload(
        status="firing",
        commonLabels={"service": "checkout-api", "severity": "critical"},
        commonAnnotations={"summary": "checkout-api HTTP 500"},
        alerts=[
            {
                "status": "firing",
                "labels": {"alertname": "DBPoolExhausted"},
                "annotations": {"description": "DB_POOL_EXHAUSTED timeout acquiring connection"},
                "fingerprint": "abc",
            }
        ],
    )

    events = grafanaPayloadToEvents(payload)

    assert len(events) == 1
    assert events[0].sourceType == "grafana-webhook"
    assert events[0].sourceId == "abc"
    assert events[0].serviceName == "checkout-api"
    assert "DBPoolExhausted" in events[0].alertTitle
    assert "DB_POOL_EXHAUSTED" in events[0].logSnippet


def testGrafanaSignatureValidationAcceptsTimestampedSignature() -> None:
    body = b'{"status":"firing"}'
    secret = "secret"
    timestamp = str(int(time.time()))
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}:".encode("utf-8") + body, hashlib.sha256).hexdigest()

    verifyGrafanaSignature(
        body,
        {
            "x-grafana-alerting-signature": digest,
            "x-grafana-alerting-signature-timestamp": timestamp,
        },
        secret,
    )


def testGrafanaSignatureValidationRejectsBadSignature() -> None:
    with pytest.raises(ValueError):
        verifyGrafanaSignature(
            b"{}",
            {"x-grafana-alerting-signature": "bad"},
            "secret",
        )
