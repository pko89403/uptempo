#!/usr/bin/env bash
# scripts/setup-bare.sh
# 기존 일반 repo를 bare repo + worktree 구조로 변환합니다.
#
# 실행 전 구조:
#   ~/PERSONAL/uptempo/          ← 일반 repo (현재 위치)
#
# 실행 후 구조:
#   ~/PERSONAL/uptempo.git/      ← bare repo (중앙 허브, 모든 ref 소유)
#   ~/PERSONAL/uptempo-trees/    ← worktree 루트
#     ├── main/                  ← main 브랜치 (orchestrator 전용)
#     └── integration/           ← 공통 변경 통합 브랜치
#
# 사용법:
#   cd ~/PERSONAL/uptempo && bash scripts/setup-bare.sh

set -euo pipefail

ORIG_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PARENT="$(dirname "$ORIG_DIR")"
BARE_DIR="${PARENT}/uptempo.git"
TREES_DIR="${PARENT}/uptempo-trees"
LOCK_DIR="${TREES_DIR}/.locks"

echo "╔══════════════════════════════════════════╗"
echo "║  Uptempo: bare repo + worktree 초기 설정  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  원본 repo:   ${ORIG_DIR}"
echo "  bare repo:   ${BARE_DIR}"
echo "  worktrees:   ${TREES_DIR}"
echo ""

if [[ -d "${BARE_DIR}" ]]; then
  echo "❌ ${BARE_DIR} 이미 존재합니다. 기존 설정을 확인하세요."
  exit 1
fi

# 1) bare clone 생성
echo "▶ bare clone 생성..."
git clone --bare "${ORIG_DIR}" "${BARE_DIR}"

# bare repo에서 origin 제거 후 실제 remote 설정
cd "${BARE_DIR}"
git remote remove origin 2>/dev/null || true
REMOTE_URL=$(git -C "${ORIG_DIR}" remote get-url origin 2>/dev/null || echo "")
if [[ -n "${REMOTE_URL}" ]]; then
  git remote add origin "${REMOTE_URL}"
  echo "  remote origin → ${REMOTE_URL}"
fi

# 2) worktree 루트 + lock 디렉토리 생성
echo "▶ worktree 루트 생성..."
mkdir -p "${TREES_DIR}" "${LOCK_DIR}"

# 3) main worktree 생성
echo "▶ main worktree 생성..."
git worktree add "${TREES_DIR}/main" main

# 4) integration 브랜치 + worktree 생성
echo "▶ integration 브랜치 생성..."
git branch integration main 2>/dev/null || true
git worktree add "${TREES_DIR}/integration" integration

# 5) 스크립트를 worktree에서도 접근 가능하도록 심볼릭 링크
for wt in main integration; do
  if [[ -d "${TREES_DIR}/${wt}/scripts" ]]; then
    echo "  scripts/ already present in ${wt}"
  fi
done

echo ""
echo "✅ 설정 완료!"
echo ""
echo "  bare repo:       ${BARE_DIR}"
echo "  main worktree:   ${TREES_DIR}/main"
echo "  integration:     ${TREES_DIR}/integration"
echo ""
echo "다음 단계:"
echo "  cd ${TREES_DIR}/main"
echo "  bash scripts/wt add feat/my-feature"
echo ""
echo "⚠️  원본 디렉토리(${ORIG_DIR})는 이제 아카이브 용도입니다."
echo "   삭제하려면: rm -rf ${ORIG_DIR}"
