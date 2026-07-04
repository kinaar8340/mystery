#!/usr/bin/env bash
# Sync, commit, push GitHub, and deploy to HF Space (SSH git).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1. Sync HF space bundle ==="
bash scripts/sync_hf_space.sh

echo "=== 2. Git commit (mystery) ==="
git add -A
git status --short
if git diff --cached --quiet; then
  echo "No staged changes"
  GH_SHA="$(git rev-parse HEAD)"
else
  git commit -m "chore: sync HF Space bundle — Gravity presets, docs, housekeeping"
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
  echo "  OR export HF_TOKEN and run: huggingface-cli repo create mystery --type space --space_sdk gradio"
  echo ""
  exit 1
fi

rsync -av --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='mystery_image.png' \
  --exclude='assets/demo_a_breathing.gif' \
  "$ROOT/space/mystery/" "$HF_DIR/"
cd "$HF_DIR"
git add -A
git status --short
if git diff --cached --quiet; then
  echo "No HF changes to commit"
  HF_SHA="$(git rev-parse HEAD)"
  HF_PUSH="no changes"
else
  git commit -m "feat: Gravity tab — unit-cell presets, deformation animation, updated README"
  HF_SHA="$(git rev-parse HEAD)"
  git push origin main
  HF_PUSH="OK"
fi

echo ""
echo "=== RESULTS ==="
echo "GITHUB_SHA=$GH_SHA"
echo "HF_SHA=$HF_SHA"
echo "HF_PUSH=$HF_PUSH"
echo "SPACE_URL=https://huggingface.co/spaces/kinaar111/mystery"