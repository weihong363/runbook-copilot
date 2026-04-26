from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from app.core.config import getSettings
from app.models.schemas import (
    GrafanaWebhookPayload,
    GrafanaWebhookResponse,
    IncidentAnalyzeRequest,
    IncidentAnalyzeResponse,
    IncidentEventRequest,
    IncidentListResponse,
    IncidentRecord,
)
from app.rag.factory import createAnswerGeneratorFromSettings, createRetriever
from app.services.grafana_adapter import countResolvedAlerts, grafanaPayloadToEvents, verifyGrafanaSignature
from app.services.incident_analyzer import IncidentAnalyzer
from app.services.incident_store import eventToAnalyzeRequest, getIncident, listIncidents, saveIncidentAnalysis

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyzeIncident(request: IncidentAnalyzeRequest) -> IncidentAnalyzeResponse:
    settings = getSettings()
    try:
        response = _analyze(request)
        incidentId = saveIncidentAnalysis(settings.databasePath, request, response)
        return response.model_copy(update={"incidentId": incidentId})
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/events", response_model=IncidentAnalyzeResponse)
def ingestIncidentEvent(request: IncidentEventRequest) -> IncidentAnalyzeResponse:
    settings = getSettings()
    try:
        response, incidentId = _ingestEvent(request)
        return response.model_copy(update={"incidentId": incidentId})
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/integrations/grafana", response_model=GrafanaWebhookResponse)
async def ingestGrafanaWebhook(request: Request) -> GrafanaWebhookResponse:
    settings = getSettings()
    try:
        rawBody = await request.body()
        headers = {key.lower(): value for key, value in request.headers.items()}
        verifyGrafanaSignature(rawBody, headers, settings.grafanaWebhookSecret)
        payload = GrafanaWebhookPayload.model_validate_json(rawBody)
        incidentIds = [_ingestEvent(event)[1] for event in grafanaPayloadToEvents(payload)]
        return GrafanaWebhookResponse(
            accepted=True,
            incidentIds=incidentIds,
            skippedResolved=countResolvedAlerts(payload),
        )
    except (ValueError, ValidationError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=IncidentListResponse)
def getIncidents(limit: int = 20) -> IncidentListResponse:
    try:
        return IncidentListResponse(incidents=listIncidents(getSettings().databasePath, limit=limit))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{incidentId}", response_model=IncidentRecord)
def getIncidentRecord(incidentId: str) -> IncidentRecord:
    try:
        incident = getIncident(getSettings().databasePath, incidentId)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if incident is None:
        raise HTTPException(status_code=404, detail="incident 不存在")
    return incident


def _analyze(request: IncidentAnalyzeRequest) -> IncidentAnalyzeResponse:
    settings = getSettings()
    retriever = createRetriever(settings)
    answerGenerator = createAnswerGeneratorFromSettings(settings)
    analyzer = IncidentAnalyzer(retriever, settings.topK, answerGenerator)
    if request.debug:
        entities, rewrittenQuery, answer, debug = analyzer.analyzeWithDebug(request)
        return IncidentAnalyzeResponse(
            entities=entities,
            rewrittenQuery=rewrittenQuery,
            answer=answer,
            debug=debug,
        )
    entities, rewrittenQuery, answer = analyzer.analyze(request)
    return IncidentAnalyzeResponse(entities=entities, rewrittenQuery=rewrittenQuery, answer=answer)


def _ingestEvent(request: IncidentEventRequest) -> tuple[IncidentAnalyzeResponse, str]:
    settings = getSettings()
    analyzeRequest = eventToAnalyzeRequest(request)
    response = _analyze(analyzeRequest)
    incidentId = saveIncidentAnalysis(
        settings.databasePath,
        analyzeRequest,
        response,
        sourceType=request.sourceType,
        sourceId=request.sourceId,
        severity=request.severity,
        labels=request.labels,
    )
    return response, incidentId
