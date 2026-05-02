"""
Confluence 웹훅 페이로드를 Discord embed 포맷으로 변환
"""

# Discord embed 색상
COLOR_PAGE_CREATED  = 0x34A853  # green
COLOR_PAGE_UPDATED  = 0x4285F4  # blue
COLOR_COMMENT       = 0xFBBC04  # yellow
COLOR_MENTION       = 0xEA3323  # red


def parse_confluence_event(body: dict) -> dict | None:
    event = body.get("event", "")

    if event == "page_created":
        return _page_created(body)
    elif event == "page_updated":
        return _page_updated(body)
    elif event == "comment_created":
        return _comment_created(body)
    else:
        return None


# ── 공통 헬퍼 ─────────────────────────────────────────────

def _author_name(user: dict) -> str:
    return user.get("displayName") or user.get("username") or "Unknown"

def _page_url(page: dict) -> str:
    links = page.get("_links", {})
    base = links.get("base", "")
    web  = links.get("webui", "")
    return base + web

def _space_name(page: dict) -> str:
    space = page.get("space", {})
    return space.get("name") or space.get("key") or "-"

def _truncate(text: str, limit: int = 200) -> str:
    return text[:limit] + "…" if len(text) > limit else text


# ── 이벤트별 embed 생성 ───────────────────────────────────

def _page_created(body: dict) -> dict:
    page   = body.get("page", {})
    author = body.get("userAccountId") or ""
    user   = body.get("creator", body.get("user", {}))

    return {
        "title": f"📄 새 페이지 생성: {page.get('title', '(제목 없음)')}",
        "url": _page_url(page),
        "color": COLOR_PAGE_CREATED,
        "fields": [
            {"name": "스페이스", "value": _space_name(page), "inline": True},
            {"name": "작성자",   "value": _author_name(user),  "inline": True},
        ],
        "footer": {"text": "Confluence"},
    }


def _page_updated(body: dict) -> dict:
    page    = body.get("page", {})
    user    = body.get("updater", body.get("user", {}))
    version = page.get("version", {})
    ver_num = version.get("number", "?")

    return {
        "title": f"✏️ 페이지 수정: {page.get('title', '(제목 없음)')}",
        "url": _page_url(page),
        "color": COLOR_PAGE_UPDATED,
        "fields": [
            {"name": "스페이스", "value": _space_name(page), "inline": True},
            {"name": "수정자",   "value": _author_name(user),  "inline": True},
            {"name": "버전",     "value": str(ver_num),         "inline": True},
        ],
        "footer": {"text": "Confluence"},
    }


def _comment_created(body: dict) -> dict:
    comment = body.get("comment", {})
    page    = comment.get("page", body.get("page", {}))
    user    = body.get("commenter", body.get("user", {}))
    raw_body = comment.get("body", {})

    # 댓글 본문 추출 (storage / view / plain 순서로 시도)
    text = (
        raw_body.get("view", {}).get("value")
        or raw_body.get("storage", {}).get("value")
        or ""
    )
    # HTML 태그 간단 제거
    import re
    text = re.sub(r"<[^>]+>", "", text).strip()

    fields = [
        {"name": "페이지",  "value": page.get("title", "-"), "inline": True},
        {"name": "스페이스","value": _space_name(page),       "inline": True},
        {"name": "작성자",  "value": _author_name(user),       "inline": True},
    ]
    if text:
        fields.append({"name": "내용", "value": _truncate(text), "inline": False})

    return {
        "title": "💬 새 댓글",
        "url": _page_url(page),
        "color": COLOR_COMMENT,
        "fields": fields,
        "footer": {"text": "Confluence"},
    }
