"""Webhook route handlers for Meta WhatsApp Business Cloud API ingestion."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from src.api.config import get_settings
from src.api.worker import InteractionWorker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])
worker = InteractionWorker()


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
) -> Response:
    """Handle Meta webhook verification challenge handshake."""
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification challenge successful.")
        return PlainTextResponse(content=hub_challenge or "", status_code=200)

    logger.warning("Webhook verification handshake failed: invalid token or mode.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("")
async def receive_webhook_event(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Ingest inbound WhatsApp messages and delegate processing to background worker."""
    correlation_id = str(uuid.uuid4())
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info("[CID:%s] Received WhatsApp webhook payload: %s", correlation_id, body)

    # Validate Meta event envelope
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                phone = msg.get("from", "")
                if phone:
                    background_tasks.add_task(
                        worker.process_inbound_message,
                        phone=phone,
                        message_data=msg,
                        correlation_id=correlation_id,
                    )

    return {"status": "EVENT_RECEIVED"}
