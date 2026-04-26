from fastapi import FastAPI

from app.api.routes.debug import router as debugRouter
from app.api.routes.feedback import router as feedbackRouter
from app.api.routes.health import router as healthRouter
from app.api.routes.incidents import router as incidentsRouter
from app.api.routes.knowledge import router as knowledgeRouter
from app.core.config import getSettings
from app.core.database import initializeDatabase


def createApp() -> FastAPI:
    settings = getSettings()
    initializeDatabase(settings.databasePath)
    app = FastAPI(title=settings.appName)
    app.include_router(healthRouter)
    app.include_router(knowledgeRouter)
    app.include_router(incidentsRouter)
    app.include_router(feedbackRouter)
    app.include_router(debugRouter)
    return app


app = createApp()
