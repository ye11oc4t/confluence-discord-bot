import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from formatters import get_formatter

app = FastAPI(title="Confluence → Discord Bot")

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CONFLUENCE_SECRET   = os.environ.get("CONFLUENCE_WEBHOOK_SECRET", "")
ALLOWED_SPACES      = [s.strip() for s in os.environ.get("ALLOWED_SPACES", "").split(",") if s.strip()]

def _extract_space_key(payload: dict) -> str | None:
    for key in ("page", "comment", "attachment", "space"):
        obj = payload.get(key, {})
        if obj:
            space = obj.get("space", {})
            return space.get("key") or None
    return None

def _verify_token(header_val: str) -> bool:
    """Confluence는 SHA256 HMAC 대신 단순 Bearer 토큰 방식 지원"""
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
    # 시크릿 토큰 검증 (설정된 경우)
    if CONFLUENCE_SECRET and not _verify_token(authorization or ""):
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = await request.json()

    # 이벤트 타입: 헤더 우선, 없으면 페이로드에서
    event = x_confluence_event or payload.get("event", "unknown")

    # 스페이스 필터링
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
