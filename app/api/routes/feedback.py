from fastapi import APIRouter

from app.core.config import getSettings
from app.models.schemas import FeedbackItem, FeedbackRequest, FeedbackResponse, FeedbackSummary
from app.services.feedback_service import listFeedback, saveFeedback, summarizeFeedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def createFeedback(request: FeedbackRequest) -> FeedbackResponse:
    feedbackId = saveFeedback(getSettings().databasePath, request)
    return FeedbackResponse(accepted=True, feedbackId=feedbackId)


@router.get("", response_model=list[FeedbackItem])
def getFeedback(incidentId: str | None = None, limit: int = 50) -> list[FeedbackItem]:
    return listFeedback(getSettings().databasePath, incidentId=incidentId, limit=limit)


@router.get("/summary", response_model=FeedbackSummary)
def getFeedbackSummary(incidentId: str | None = None) -> FeedbackSummary:
    return summarizeFeedback(getSettings().databasePath, incidentId=incidentId)
