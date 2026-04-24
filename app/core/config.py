from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    appName: str = Field(default="runbook-copilot")
    knowledgeDir: Path = Field(default=Path("knowledge"))
    dataDir: Path = Field(default=Path("data"))
    databasePath: Path = Field(default=Path("data/runbook_copilot.sqlite3"))
    vectorDimension: int = Field(default=128, ge=16)
    topK: int = Field(default=5, ge=1, le=20)


@lru_cache
def getSettings() -> Settings:
    load_dotenv()
    return Settings(
        appName=os.getenv("APP_NAME", "runbook-copilot"),
        knowledgeDir=Path(os.getenv("KNOWLEDGE_DIR", "knowledge")),
        dataDir=Path(os.getenv("DATA_DIR", "data")),
        databasePath=Path(os.getenv("DATABASE_PATH", "data/runbook_copilot.sqlite3")),
        vectorDimension=int(os.getenv("VECTOR_DIMENSION", "128")),
        topK=int(os.getenv("TOP_K", "5")),
    )
