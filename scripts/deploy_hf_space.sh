#!/usr/bin/env bash
# Sync, commit, push GitHub, and deploy to HF Space (SSH git).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMMIT_MSG="${1:-feat: sync HF Space — Stage 6 results, analog UI, build stamp}"

echo "=== 1. Sync HF space bundle ==="
bash scripts/sync_hf_space.sh

echo "=== 2. Git commit (mystery) ==="
git add -A
git status --short
if git diff --cached --quiet; then
  echo "No staged changes"
  GH_SHA="$(git rev-parse HEAD)"
else
  git commit -m "$COMMIT_MSG"
  GH_SHA="$(git rev-parse HEAD)"
fi
echo "GitHub SHA: $GH_SHA"

echo "=== 3. Git push origin main ==="
git push origin main

echo "=== 4. Deploy to HF Space ==="
HF_DIR="/tmp/hf-mystery"
rm -rf "$HF_DIR"

if ! git clone git@hf.co:spaces/kinaar111/mystery "$HF_DIR" 2>/dev/null; then
  echo ""
  echo "HF Space repo not found. Create it first:"
  echo "  1. Visit https://huggingface.co/new-space"
  echo "  2. Owner: kinaar111, Name: mystery, SDK: Gradio"
  echo "  OR: hf repo create mystery --type space --space_sdk gradio"
  echo ""
  exit 1
fi

# Large binaries: never overwrite from local rsync (HF requires Xet/LFS for mp4).
RSYNC_EXCLUDES=(
  --exclude='.git'
  --exclude='.gradio'
  --exclude='.venv'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='mystery_image.png'
  --exclude='bg1_mystery.png'
  --exclude='backup_mystery_image.png'
  --exclude='assets/*.mp4'
  --exclude='assets/*.gif'
  --exclude='assets/demo_a_breathing.gif'
  --exclude='assets/home_a_startup_page.png'
)

rsync -av --delete "${RSYNC_EXCLUDES[@]}" "$ROOT/space/mystery/" "$HF_DIR/"
rm -rf "$HF_DIR/.gradio"
cd "$HF_DIR"

# Restore Xet/LFS-tracked binaries (never overwrite from local rsync).
for asset in assets/*.mp4 assets/*.gif; do
  [[ -e "$asset" ]] || continue
  if git ls-files --error-unmatch "$asset" &>/dev/null; then
    git checkout HEAD -- "$asset" 2>/dev/null || true
  fi
done

git add -A
git status --short
if git diff --cached --quiet; then
  echo "No HF changes to commit"
  HF_SHA="$(git rev-parse HEAD)"
  HF_PUSH="no changes"
else
  git commit -m "$COMMIT_MSG"
  HF_SHA="$(git rev-parse HEAD)"
  if git push origin main; then
    HF_PUSH="OK"
  else
    echo ""
    echo "HF push failed — if binary assets were included, enable Xet:"
    echo "  curl -sSf https://raw.githubusercontent.com/huggingface/xet-core/main/git_xet/install.sh | sh"
    echo "  git xet install"
    echo "  git add assets/*.mp4 && git commit -m 'Enable Xet for demo videos' && git push"
    HF_PUSH="FAILED"
    exit 1
  fi
fi

echo ""
echo "=== RESULTS ==="
echo "GITHUB_SHA=$GH_SHA"
echo "HF_SHA=$HF_SHA"
echo "HF_PUSH=$HF_PUSH"
echo "SPACE_URL=https://huggingface.co/spaces/kinaar111/mystery"