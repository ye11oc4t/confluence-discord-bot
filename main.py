import os
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from formatters import get_formatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")

app = FastAPI(title="Confluence → Discord Bot")

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CONFLUENCE_SECRET   = os.environ.get("CONFLUENCE_WEBHOOK_SECRET", "")
ALLOWED_SPACES      = [s.strip() for s in os.environ.get("ALLOWED_SPACES", "").split(",") if s.strip()]

def _infer_event(payload: dict, header_event: Optional[str]) -> str:
    if header_event:
        return header_event
    if e := payload.get("event"):
        return e
    if t := payload.get("updateTrigger"):
        return t
    if "comment" in payload:
        return "comment_created"
    if "attachment" in payload:
        return "attachment_created"
    if "space" in payload and "page" not in payload:
        return "space_created"
    if "page" in payload:
        return "page_created"
    return "unknown"

def _extract_space_key(payload: dict) -> str | None:
    for key in ("page", "comment", "attachment", "space"):
        obj = payload.get(key, {})
        if obj:
            space = obj.get("space", {})
            return space.get("key") or obj.get("spaceKey") or None
    return None

def _verify_token(header_val: str) -> bool:
    if not CONFLUENCE_SECRET:
        return True
    return CONFLUENCE_SECRET in (header_val or "")

@app.get("/")
async def health():
    return {"status": "ok", "message": "Confluence Discord Bot is running"}

@app.post("/webhook")
async def confluence_webhook(
    request: Request,
    x_confluence_event: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    if CONFLUENCE_SECRET and not _verify_token(authorization or ""):
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = await request.json()
    event = _infer_event(payload, x_confluence_event)

    if event == "unknown":
        logger.info(f"unknown 스킵: {list(payload.keys())}")
        return {"status": "skipped", "event": "unknown"}

    logger.info(f"Received event: {event}")

    if ALLOWED_SPACES:
        space_key = _extract_space_key(payload)
        if space_key and space_key not in ALLOWED_SPACES:
            return {"status": "filtered", "event": event, "space": space_key}

    formatter = get_formatter(event)
    embed = formatter(payload, event)

    if embed is None:
        return {"status": "skipped", "event": event}

    async with httpx.AsyncClient() as client:
        resp = await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        resp.raise_for_status()

    return {"status": "ok", "event": event}
