# Confluence → Discord 알림 봇

Confluence Webhook 이벤트를 Discord 채널에 Embed로 전송하는 Webhook 서버.

## 지원 이벤트

| 이벤트 | 설명 | 색상 |
|--------|------|------|
| `page_created` | 페이지 생성 | 🟢 Green |
| `page_updated` | 페이지 수정 | 🔵 Blue |
| `page_trashed` | 페이지 삭제(휴지통) | 🔴 Red |
| `page_restored` | 페이지 복원 | 🟢 Green |
| `page_children_reordered` | 페이지 이동 | 🟡 Yellow |
| `comment_created` | 댓글 생성 | 🟡 Yellow |
| `comment_updated` | 댓글 수정 | 🔵 Blue |
| `comment_removed` | 댓글 삭제 | 🔴 Red |
| `attachment_created` | 첨부파일 업로드 | 🔵 Blue |
| `space_created` | 스페이스 생성 | 🟢 Green |

---

## 배포 방법

### 1. Discord Webhook URL 생성
1. Discord 채널 → 설정 → 연동 → **웹후크 만들기**
2. URL 복사

### 2. Railway 배포

```bash
git init && git add . && git commit -m "init"
gh repo create confluence-discord-bot --private --push
# railway.app → New Project → GitHub repo 선택
```

환경변수:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
CONFLUENCE_WEBHOOK_SECRET=your_secret   # 선택
ALLOWED_SPACES=WB,CERT                  # 비어있으면 전체 허용
```

---

## Confluence Webhook 설정

1. Confluence 관리자 → **일반 구성** → **웹훅** → **웹훅 만들기**
2. Payload URL: `https://your-app.railway.app/webhook`
3. 이벤트 선택 후 저장

---

## 로컬 테스트

```bash
pip install -r requirements.txt
cp .env.example .env

uvicorn main:app --reload

curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Confluence-Event: page_created" \
  -d '{
    "event": "page_created",
    "page": {
      "title": "테스트 페이지",
      "space": {"key": "WB", "name": "Woowa Beavers"},
      "_links": {"base": "https://your-domain.atlassian.net", "webui": "/wiki/spaces/WB/pages/123"}
    },
    "actor": {"displayName": "김서연"}
  }'
```

---

## 파일 구조

```
confluence-discord-bot/
├── main.py          # FastAPI 서버, 토큰 검증, 스페이스 필터링, Discord 전송
├── formatters.py    # 이벤트별 Discord Embed 포맷터
├── requirements.txt
├── Procfile
├── railway.toml
└── .env.example
```
