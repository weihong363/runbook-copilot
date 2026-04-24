from fastapi import APIRouter

from app.core.config import getSettings
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import saveFeedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def createFeedback(request: FeedbackRequest) -> FeedbackResponse:
    feedbackId = saveFeedback(getSettings().databasePath, request)
    return FeedbackResponse(accepted=True, feedbackId=feedbackId)
