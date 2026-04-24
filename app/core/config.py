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


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def getSettings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        appName=os.getenv("APP_NAME", "runbook-copilot"),
        knowledgeDir=_resolveProjectPath(os.getenv("KNOWLEDGE_DIR", "knowledge")),
        dataDir=_resolveProjectPath(os.getenv("DATA_DIR", "data")),
        databasePath=_resolveProjectPath(os.getenv("DATABASE_PATH", "data/runbook_copilot.sqlite3")),
        vectorDimension=int(os.getenv("VECTOR_DIMENSION", "128")),
        topK=int(os.getenv("TOP_K", "5")),
    )


def _resolveProjectPath(rawPath: str) -> Path:
    path = Path(rawPath).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
