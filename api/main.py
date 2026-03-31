"""Uptempo FastAPI backend — schema metadata API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Uptempo Schema API",
    description="REST endpoints for gRPC/Thrift/WebSocket schema metadata",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# TODO: mount schema router — parse generated OpenAPI schemas, expose
#       services/methods/message-structure endpoints.
# from api.routers import schemas
# app.include_router(schemas.router, prefix="/schemas", tags=["schemas"])

# TODO: mount orchestrator router — trigger and inspect workflow runs.
# from api.routers import orchestrator
# app.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])

# TODO: mount workspace router — list / manage generated workspaces.
# from api.routers import workspace
# app.include_router(workspace.router, prefix="/workspaces", tags=["workspaces"])
