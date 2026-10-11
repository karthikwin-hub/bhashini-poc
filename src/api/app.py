"""FastAPI application for Bhashini Sovereign Multilingual Platform."""

from fastapi import FastAPI

from src.api.routes.webhook import router as webhook_router

app = FastAPI(
    title="Bhashini Sovereign Multilingual Service",
    description="Multilingual speech, translation, and messaging service powered by Bhashini DPI",
    version="0.1.0",
)

app.include_router(webhook_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify service liveness."""
    return {"status": "ok", "service": "bhashini-app"}
