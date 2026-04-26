from pydantic import BaseModel, Field, field_validator, model_validator


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
    debug: bool = False

    @field_validator("alertTitle", "serviceName", "logSnippet", mode="before")
    @classmethod
    def stripRequiredText(cls, value: str) -> str:
        if value is None:
            raise ValueError("字段不能为空")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("字段不能为空白")
        return normalized

    @field_validator("symptomDescription", mode="before")
    @classmethod
    def stripOptionalText(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class ExtractedEntities(BaseModel):
    service: str
    dependencies: list[str] = Field(default_factory=list)
    exceptionTypes: list[str] = Field(default_factory=list)
    errorCodes: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    symptomTags: list[str] = Field(default_factory=list)


class RetrievalFilters(BaseModel):
    service: str | None = None
    docTypes: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    errorCodes: list[str] = Field(default_factory=list)


class QueryRewrite(BaseModel):
    keywordQuery: str
    semanticQuery: str
    filters: RetrievalFilters


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


class RetrievalDebugItem(BaseModel):
    chunkId: str
    title: str
    path: str
    heading: str
    docType: str
    service: str
    vectorScore: float
    bm25Score: float
    bm25Normalized: float
    rerankBoost: float
    finalScore: float
    rerankReasons: list[str] = Field(default_factory=list)


class RetrievalDebug(BaseModel):
    totalChunks: int
    filteredChunks: int
    appliedFilters: RetrievalFilters
    stages: list[str] = Field(default_factory=list)
    candidates: list[RetrievalDebugItem] = Field(default_factory=list)


class AnswerGenerationDebug(BaseModel):
    provider: str
    promptVersion: str
    usedLlm: bool
    warnings: list[str] = Field(default_factory=list)


class IncidentAnalyzeDebug(BaseModel):
    entities: ExtractedEntities
    rewrittenQuery: QueryRewrite
    retrieval: RetrievalDebug
    answerGeneration: AnswerGenerationDebug | None = None


class IncidentAnalyzeResponse(BaseModel):
    incidentId: str | None = None
    entities: ExtractedEntities
    rewrittenQuery: QueryRewrite
    answer: TroubleshootingResponse
    debug: IncidentAnalyzeDebug | None = None


class IngestResponse(BaseModel):
    indexedDocuments: int
    indexedChunks: int
    indexedByDocType: dict[str, int] = Field(default_factory=dict)
    emptySectionsMerged: int = 0
    indexedFiles: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    incidentId: str | None = Field(default=None, max_length=120)
    rating: int = Field(ge=1, le=5)
    useful: bool | None = None
    reason: str | None = Field(default=None, max_length=120)
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    accepted: bool
    feedbackId: int


class FeedbackItem(BaseModel):
    feedbackId: int
    incidentId: str | None
    rating: int
    useful: bool | None
    reason: str | None
    comment: str | None
    createdAt: str


class FeedbackSummary(BaseModel):
    total: int
    averageRating: float | None
    usefulCount: int
    notUsefulCount: int


class IncidentEventRequest(BaseModel):
    sourceType: str = Field(default="manual", min_length=1, max_length=80)
    sourceId: str | None = Field(default=None, max_length=160)
    alertTitle: str = Field(min_length=1, max_length=300)
    serviceName: str = Field(min_length=1, max_length=120)
    logSnippet: str = Field(min_length=1, max_length=4000)
    symptomDescription: str | None = Field(default=None, max_length=1000)
    severity: str | None = Field(default=None, max_length=40)
    labels: dict[str, str] = Field(default_factory=dict)
    debug: bool = False

    @field_validator("sourceType", "alertTitle", "serviceName", "logSnippet", mode="before")
    @classmethod
    def stripRequiredEventText(cls, value: str) -> str:
        if value is None:
            raise ValueError("字段不能为空")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("字段不能为空白")
        return normalized

    @field_validator("sourceId", "symptomDescription", "severity", mode="before")
    @classmethod
    def stripOptionalEventText(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class IncidentRecord(BaseModel):
    incidentId: str
    sourceType: str
    sourceId: str | None
    alertTitle: str
    serviceName: str
    severity: str | None
    status: str
    labels: dict[str, str]
    answer: TroubleshootingResponse
    createdAt: str
    updatedAt: str


class IncidentListResponse(BaseModel):
    incidents: list[IncidentRecord]


class GrafanaAlert(BaseModel):
    status: str = Field(default="firing", max_length=40)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None
    endsAt: str | None = None
    generatorURL: str | None = None
    fingerprint: str | None = None


class GrafanaWebhookPayload(BaseModel):
    receiver: str | None = None
    status: str = Field(default="firing", max_length=40)
    alerts: list[GrafanaAlert] = Field(default_factory=list)
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = None
    version: str | None = None
    groupKey: str | None = None
    title: str | None = None
    message: str | None = None


class GrafanaWebhookResponse(BaseModel):
    accepted: bool
    incidentIds: list[str]
    skippedResolved: int = 0
