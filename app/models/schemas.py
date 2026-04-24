from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    chunkId: str
    title: str
    path: str
    heading: str
    score: float = Field(ge=0)
    excerpt: str


class IncidentAnalyzeRequest(BaseModel):
    alertTitle: str = Field(min_length=1, max_length=300)
    serviceName: str = Field(min_length=1, max_length=120)
    logSnippet: str = Field(min_length=1, max_length=4000)
    symptomDescription: str | None = Field(default=None, max_length=1000)


class ExtractedEntities(BaseModel):
    service: str
    errorCodes: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class TroubleshootingResponse(BaseModel):
    summary: str
    likelyCauses: list[str]
    steps: list[str]
    citations: list[Citation]
    nextAction: str

    @model_validator(mode="after")
    def ensureUsefulAnswer(self) -> "TroubleshootingResponse":
        if not self.summary.strip():
            raise ValueError("summary 不能为空")
        if not self.steps:
            raise ValueError("steps 至少需要一条")
        return self


class IncidentAnalyzeResponse(BaseModel):
    entities: ExtractedEntities
    rewrittenQuery: str
    answer: TroubleshootingResponse


class IngestResponse(BaseModel):
    indexedDocuments: int
    indexedChunks: int


class FeedbackRequest(BaseModel):
    incidentId: str | None = Field(default=None, max_length=120)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    accepted: bool
    feedbackId: int
