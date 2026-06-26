from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.exceptions import AppException
from app.models.base import Base
from app.modules.project.api import router as project_router
from app.modules.ticket.api.routes import router as ticket_router
from app.modules.ticket.service.ticket_queue import ticket_queue


SQLITE_TICKET_COLUMNS = {
    "repository_path": "VARCHAR(500)",
    "ticket_type": "VARCHAR(30) NOT NULL DEFAULT 'request'",
    "complexity": "VARCHAR(20) NOT NULL DEFAULT 'low'",
    "requester_name": "VARCHAR(255)",
    "review_status": "VARCHAR(30) NOT NULL DEFAULT 'not_required'",
    "approved_by": "VARCHAR(255)",
    "execution_log": "TEXT",
    "diff": "TEXT",
    "queued_at": "DATETIME",
    "started_at": "DATETIME",
    "completed_at": "DATETIME",
}


async def _ensure_sqlite_schema() -> None:
    if engine.dialect.name != "sqlite":
        return
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(tickets)"))
        existing_columns = {row[1] for row in result.fetchall()}
        for column_name, column_type in SQLITE_TICKET_COLUMNS.items():
            if column_name not in existing_columns:
                await conn.execute(
                    text(f"ALTER TABLE tickets ADD COLUMN {column_name} {column_type}")
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_sqlite_schema()
    ticket_queue.start()
    yield
    await ticket_queue.stop()


app = FastAPI(title="AI Assistant Code", lifespan=lifespan)

app.include_router(ticket_router, prefix="/api")
app.include_router(project_router, prefix="/api")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
