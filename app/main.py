from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import logging
from app.parser import parse_confluence_event
from app.filters import should_notify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Confluence Discord Bot")

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
ALLOWED_SPACES = os.environ.get("ALLOWED_SPACES", "")  # 콤마 구분, 비어있으면 전체 허용
SECRET_TOKEN = os.environ.get("CONFLUENCE_SECRET_TOKEN", "")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def confluence_webhook(request: Request):
    # 선택적 시크릿 토큰 검증
    if SECRET_TOKEN:
        token = request.headers.get("X-Hub-Signature") or request.headers.get("Authorization", "")
        if SECRET_TOKEN not in token:
            raise HTTPException(status_code=401, detail="Invalid token")

    body = await request.json()
    logger.info(f"Received event: {body.get('event', 'unknown')}")

    allowed_spaces = [s.strip() for s in ALLOWED_SPACES.split(",") if s.strip()]

    if not should_notify(body, allowed_spaces):
        return JSONResponse({"status": "filtered"})

    embed = parse_confluence_event(body)
    if not embed:
        return JSONResponse({"status": "ignored"})

    async with httpx.AsyncClient() as client:
        resp = await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        if resp.status_code not in (200, 204):
            logger.error(f"Discord webhook failed: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=502, detail="Discord webhook failed")

    return JSONResponse({"status": "sent"})
