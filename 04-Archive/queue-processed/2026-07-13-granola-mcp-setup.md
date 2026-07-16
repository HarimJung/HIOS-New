---
type: action-completed
action: granola-mcp-setup
status: completed
created: 2026-07-13
completed: 2026-07-13
tags: [queue, granola, mcp]
priority: high
---

# Granola MCP 설정 완료 ✅

## 완료 상태
✅ MCP config 추가됨: `~/Library/Application Support/Claude/claude_desktop_config.json`
✅ Granola MCP 서버 URL 설정: `https://mcp.granola.ai/mcp`
✅ `granola_sync.py` DEPRECATED 표시 추가

## 다음 단계

### 1. Claude Desktop 재시작 (필수)
```bash
# Claude Desktop 앱을 완전히 종료했다가 다시 실행
# MCP 서버는 앱 시작 시에만 로드됨
```

### 2. MCP 연결 확인
Claude Desktop 재시작 후 MCP 도구 사용 가능 확인:
- `granola_get_meetings` - 미팅 목록 조회
- `granola_get_meeting` - 특정 미팅 노트 가져오기
- `granola_get_transcript` - 트랜스크립트 가져오기

### 3. `/meeting` 커맨드 업데이트
Granola MCP 도구를 사용하도록 `/meeting` 워크플로우 수정

### 4. `/process-inbox` 워크플로우 업데이트 (선택)
자동 동기화 필요하면 MCP를 사용한 새 스크립트 작성

## 백그라운드
- 문제: Granola 토큰 만료 → sync 스크립트 실패
- 원인: Granola v7+가 credential 암호화 시작
- 해결: MCP 서버 사용 (API key 방식도 가능)

자세한 내용: `05-AI/2026-07-13-granola-sync-troubleshooting.md`
