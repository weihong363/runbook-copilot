from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["debug"])

DEBUG_PAGE = Path(__file__).resolve().parents[2] / "static" / "debug.html"


@router.get("/debug", response_class=HTMLResponse)
def debugPage() -> HTMLResponse:
    return HTMLResponse(DEBUG_PAGE.read_text(encoding="utf-8"))
