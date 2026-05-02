"""
알림을 보낼지 여부를 결정하는 필터 로직
"""

SUPPORTED_EVENTS = {
    "page_created",
    "page_updated",
    "comment_created",
    "page_children_reordered",  # 페이지 이동
}

def should_notify(body: dict, allowed_spaces: list[str]) -> bool:
    event = body.get("event", "")

    if event not in SUPPORTED_EVENTS:
        return False

    # 스페이스 필터링
    if allowed_spaces:
        space_key = _extract_space_key(body)
        if space_key and space_key not in allowed_spaces:
            return False

    return True


def _extract_space_key(body: dict) -> str | None:
    # page 이벤트
    page = body.get("page", {})
    if page:
        return page.get("space", {}).get("key")

    # comment 이벤트
    comment = body.get("comment", {})
    if comment:
        return comment.get("space", {}).get("key")

    return None
