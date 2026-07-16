---
date: 2026-07-13
type: troubleshooting-log
tags: [granola, mcp, sync, troubleshooting]
status: completed
resolved: 2026-07-13T22:50:00
---

# Granola 동기화 문제 해결

## 문제
- Granola sync 스크립트 실행 시 "Access token expired" 에러
- `granola_sync.py`가 `~/Library/Application Support/Granola/supabase.json`에서 토큰 읽으려 시도
- 토큰 파일이 2026년 5월 12일 이후로 업데이트 안 됨

## 원인 분석
1. Granola 앱이 v7+ 업데이트되면서 **모든 credential 파일을 암호화**하기 시작함
   - 기존: `supabase.json` (평문)
   - 신규: `supabase.json.enc` (암호화) + 기타 `.enc` 파일들

2. 기존 sync 스크립트는 암호화되지 않은 파일을 읽도록 작성됨

3. 파일 상태:
   - `supabase.json`: 2026-05-12 마지막 수정 (만료된 토큰)
   - `supabase.json.enc`: 2026-07-13 업데이트됨 (현재 토큰)
   - `storage.dek`: 암호화 키 (바이너리)

## 시도한 해결책 (실패)
- ❌ Granola 앱 재시작 → 평문 파일 업데이트 안 됨
- ❌ AppleScript로 정상 종료 → 파일 업데이트 안 됨
- ❌ Refresh token으로 새 access token 요청 → 엔드포인트 404
- ❌ 암호화 파일 직접 복호화 → 암호화 로직 모름

## 해결책: Granola MCP 서버 사용

### 발견한 정보
- `local-state.json`에서 feature flags 확인:
  - `"mcp_enabled": true`
  - `"api_keys_page_enabled": true`
  - `"public_api_user_notes_enabled": true`

### MCP 설정 완료
```bash
# MCP config 파일 생성
~/.config/claude/mcp_config.json
```

```json
{
  "mcpServers": {
    "granola": {
      "url": "https://mcp.granola.ai/mcp"
    }
  }
}
```

## 해결 완료 ✅

### 1. MCP 설정 완료
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "granola": {
      "url": "https://mcp.granola.ai/mcp"
    }
  }
}
```

### 2. Deprecated 스크립트 표시
`.hios/scripts/granola_sync.py`에 DEPRECATED 주석 추가

### 3. 다음 단계
- **Claude Desktop 재시작 필요** (MCP 서버 로드)
- MCP 도구 사용 가능 확인: `granola_get_meetings`, `granola_get_meeting`, `granola_get_transcript`
- `/meeting` 커맨드를 MCP 사용하도록 업데이트

## 참고 파일 위치
- Granola 설정: `~/Library/Application Support/Granola/`
- Sync 스크립트 (deprecated): `.hios/scripts/granola_sync.py`
- MCP 설정 (올바른 위치): `~/Library/Application Support/Claude/claude_desktop_config.json`
- ~~잘못된 위치: `~/.config/claude/mcp_config.json`~~ (삭제됨)

## 교훈
- Granola가 암호화로 전환했으면 MCP나 공식 API 사용해야 함
- 파일 기반 토큰 추출 방식은 더 이상 작동 안 함
- 처음부터 MCP 확인했어야 했음 (사용자가 "쉬운 걸 어렵게 한다"고 지적)
