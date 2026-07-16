#!/bin/bash
# HiOS Control Center — one-command launcher
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8787
URL="http://127.0.0.1:${PORT}"

# Already running? Just open the browser.
if curl -s -m 1 "${URL}/api/health" >/dev/null 2>&1; then
  echo "HiOS Control Center 이미 실행 중 — 브라우저 오픈"
  open "${URL}"
  exit 0
fi

echo "HiOS Control Center 서버 기동 중..."
python3 "${DIR}/server.py" &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" 2>/dev/null || true' INT TERM

# Health poll: 0.5s x max 10s
for _ in $(seq 1 20); do
  if curl -s -m 1 "${URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -s -m 1 "${URL}/api/health" >/dev/null 2>&1; then
  echo "서버 기동 실패 — 로그를 확인하세요" >&2
  kill "${SERVER_PID}" 2>/dev/null || true
  exit 1
fi

echo "실행 완료: ${URL} (Ctrl-C로 종료)"
open "${URL}"
wait "${SERVER_PID}"
