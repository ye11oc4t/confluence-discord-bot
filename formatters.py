"""
Confluence Webhook 이벤트 → Discord Embed 포맷터
GitHub bot(formatters.py)과 동일한 구조로 작성
"""

COLOR = {
    "page_created":          0x34A853,  # green
    "page_updated":          0x4285F4,  # blue
    "page_trashed":          0xEA3323,  # red
    "page_restored":         0x34A853,  # green
    "page_moved":            0xFBBC04,  # yellow
    "comment_created":       0xFBBC04,  # yellow
    "comment_updated":       0x4285F4,  # blue
    "comment_removed":       0xEA3323,  # red
    "attachment_created":    0x4285F4,  # blue
    "space_created":         0x34A853,  # green
    "default":               0x7F8C8D,
}

def _user(p) -> dict:
    u = p.get("actor") or p.get("user") or p.get("creator") or p.get("updater") or p.get("commenter") or {}
    return {
        "name":     u.get("displayName") or u.get("username") or "Unknown",
        "icon_url": u.get("avatarUrl") or u.get("profilePicture", {}).get("path", ""),
        "url":      u.get("profilePageUrl") or "",
    }

def _page_url(page: dict) -> str:
    # 직접 self URL이 있으면 사용
    self_url = page.get("self", "")
    if self_url:
        return self_url
    links = page.get("_links", {})
    base = links.get("base", "")
    web  = links.get("webui", "")
    return base + web if base else web

def _space(obj: dict) -> str:
    space = obj.get("space", {})
    return space.get("name") or space.get("key") or obj.get("spaceKey") or "-"

def _trunc(text: str, n: int = 300) -> str:
    if not text: return "_없음_"
    import re
    text = re.sub(r"<[^>]+>", "", text).strip()
    return text[:n] + ("…" if len(text) > n else "")

def _version(page: dict) -> str:
    v = page.get("version", {})
    if isinstance(v, dict):
        return str(v.get("number", "?"))
    return str(v) if v else "?"

def format_page_created(p, event):
    page = p.get("page", {})
    return {"title": f"📄 새 페이지 생성: {page.get('title', '(제목 없음)')}", "url": _page_url(page), "color": COLOR["page_created"], "fields": [{"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Page Created • {_space(page)}"}}

def format_page_updated(p, event):
    page = p.get("page", {})
    return {"title": f"✏️ 페이지 수정: {page.get('title', '(제목 없음)')}", "url": _page_url(page), "color": COLOR["page_updated"], "fields": [{"name": "스페이스", "value": _space(page), "inline": True}, {"name": "버전", "value": _version(page), "inline": True}], "author": _user(p), "footer": {"text": f"Page Updated • {_space(page)}"}}

def format_page_trashed(p, event):
    page = p.get("page", {})
    return {"title": f"🗑️ 페이지 삭제: {page.get('title', '(제목 없음)')}", "url": _page_url(page), "color": COLOR["page_trashed"], "fields": [{"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Page Trashed • {_space(page)}"}}

def format_page_restored(p, event):
    page = p.get("page", {})
    return {"title": f"♻️ 페이지 복원: {page.get('title', '(제목 없음)')}", "url": _page_url(page), "color": COLOR["page_restored"], "fields": [{"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Page Restored • {_space(page)}"}}

def format_page_moved(p, event):
    page = p.get("page", {})
    old_title = (p.get("previousParent") or {}).get("title", "?")
    new_title = page.get("parent", {}).get("title", "?")
    return {"title": f"📂 페이지 이동: {page.get('title', '(제목 없음)')}", "url": _page_url(page), "color": COLOR["page_moved"], "fields": [{"name": "스페이스", "value": _space(page), "inline": True}, {"name": "이전 위치", "value": old_title, "inline": True}, {"name": "새 위치", "value": new_title, "inline": True}], "author": _user(p), "footer": {"text": f"Page Moved • {_space(page)}"}}

def format_comment_created(p, event):
    comment = p.get("comment", {})
    page = comment.get("parent", comment.get("page", p.get("page", {})))
    raw = comment.get("body", {})
    text = raw.get("view", {}).get("value") or raw.get("storage", {}).get("value") or ""
    fields = [
        {"name": "페이지",   "value": page.get("title", "-"),    "inline": True},
        {"name": "스페이스", "value": page.get("spaceKey", "-"), "inline": True},
    ]
    if text:
        fields.append({"name": "내용", "value": _trunc(text, 200), "inline": False})
    return {
        "title":  "💬 새 댓글",
        "url":    comment.get("self", _page_url(page)),
        "color":  COLOR["comment_created"],
        "fields": fields,
        "author": _user(p),
        "footer": {"text": f"Comment • {page.get('spaceKey', '-')}"},
    }


def format_comment_updated(p, event):
    comment = p.get("comment", {})
    page = comment.get("page", p.get("page", {}))
    return {"title": "✏️ 댓글 수정", "url": _page_url(page), "color": COLOR["comment_updated"], "fields": [{"name": "페이지", "value": page.get("title", "-"), "inline": True}, {"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Comment Updated • {_space(page)}"}}

def format_comment_removed(p, event):
    comment = p.get("comment", {})
    page = comment.get("page", p.get("page", {}))
    return {"title": "🗑️ 댓글 삭제", "url": _page_url(page), "color": COLOR["comment_removed"], "fields": [{"name": "페이지", "value": page.get("title", "-"), "inline": True}, {"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Comment Removed • {_space(page)}"}}

def format_attachment_created(p, event):
    attachment = p.get("attachment", {})
    page = attachment.get("page", p.get("page", {}))
    return {"title": f"📎 첨부파일: {attachment.get('title', '?')}", "url": _page_url(page), "color": COLOR["attachment_created"], "fields": [{"name": "페이지", "value": page.get("title", "-"), "inline": True}, {"name": "스페이스", "value": _space(page), "inline": True}], "author": _user(p), "footer": {"text": f"Attachment • {_space(page)}"}}

def format_space_created(p, event):
    space = p.get("space", {})
    return {"title": f"🗂️ 새 스페이스: {space.get('name', '?')}", "color": COLOR["space_created"], "fields": [{"name": "키", "value": space.get("key", "-"), "inline": True}], "author": _user(p), "footer": {"text": "Space Created"}}

def format_default(p, event):
    page = p.get("page", {})
    return {"title": f"⚡ {event}", "color": COLOR["default"], "description": f"Confluence 이벤트: `{event}`", "url": _page_url(page) or None, "fields": [{"name": "스페이스", "value": _space(page) or "-", "inline": True}], "author": _user(p), "footer": {"text": event}}

DISPATCH = {
    "page_created":            format_page_created,
    "create_page":             format_page_created,
    "page_updated":            format_page_updated,
    "edit_page":               format_page_updated,
    "page_trashed":            format_page_trashed,
    "page_restored":           format_page_restored,
    "page_children_reordered": format_page_moved,
    "comment_created":         format_comment_created,
    "comment_updated":         format_comment_updated,
    "comment_removed":         format_comment_removed,
    "attachment_created":      format_attachment_created,
    "space_created":           format_space_created,
}

def get_formatter(event: str):
    return DISPATCH.get(event, format_default)
    return DISPATCH.get(event, format_default)
