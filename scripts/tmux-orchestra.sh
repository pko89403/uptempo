#!/usr/bin/env bash
# scripts/tmux-orchestra.sh
# 전체 에이전트 오케스트레이션 tmux 레이아웃을 한 번에 구성합니다.
#
# 사용법:
#   bash scripts/tmux-orchestra.sh feat/orchestrator feat/schema-openapi feat/schema-proto
#
# 결과:
#   ┌────────────────────────────────────┐
#   │ main (orchestrator view)           │ ← pane 0: wt list 등 모니터링
#   ├──────────────────┬─────────────────┤
#   │ feat/orchestrator│ feat/schema-*   │ ← pane 1..N: 각 브랜치 에이전트
#   └──────────────────┴─────────────────┘

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WT="${SCRIPT_DIR}/wt"

SESSION="uptempo-orchestra"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "▶ 기존 오케스트레이션 세션에 연결..."
  tmux attach-session -t "$SESSION"
  exit 0
fi

if [[ $# -eq 0 ]]; then
  echo "사용법: tmux-orchestra.sh <branch1> [branch2] [branch3] ..."
  echo ""
  echo "예시:"
  echo "  bash scripts/tmux-orchestra.sh feat/orchestrator feat/schema-openapi feat/schema-proto"
  exit 1
fi

BRANCHES=("$@")

TREES_DIR="$(dirname "$(cd "$(dirname "$0")/.." && pwd)")/uptempo-trees"
BARE_DIR="$(dirname "$(cd "$(dirname "$0")/.." && pwd)")/uptempo.git"

# worktree 생성 (없으면)
for branch in "${BRANCHES[@]}"; do
  dir_name="$(echo "$branch" | tr '/' '-')"
  if [[ ! -d "${TREES_DIR}/${dir_name}" ]]; then
    echo "▶ worktree 생성: ${branch}"
    bash "$WT" add "$branch"
  fi
done

# tmux 세션 구성
echo "▶ tmux 오케스트레이션 세션 구성..."

# pane 0: 모니터링용 main worktree
tmux new-session -d -s "$SESSION" -c "${TREES_DIR}/main" \
  -x "$(tput cols)" -y "$(tput lines)"
tmux send-keys -t "$SESSION" "echo '🎼 Uptempo Orchestra — main (monitor)' && bash scripts/wt list" Enter

# 각 브랜치별 pane 생성
for branch in "${BRANCHES[@]}"; do
  dir_name="$(echo "$branch" | tr '/' '-')"
  wt_path="${TREES_DIR}/${dir_name}"

  tmux split-window -t "$SESSION" -h -c "$wt_path"
  tmux send-keys -t "$SESSION" "echo '🚀 Agent: ${branch}' && copilot" Enter
done

# 레이아웃 정리
tmux select-layout -t "$SESSION" tiled
tmux select-pane -t "$SESSION:0.0"

echo "✅ 오케스트레이션 세션 준비 완료"
echo ""
echo "  연결:  tmux attach -t ${SESSION}"
echo "  종료:  tmux kill-session -t ${SESSION}"

tmux attach-session -t "$SESSION"
