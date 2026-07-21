#!/bin/bash
# Archive the Cardioid Resonance development cycle (2026-07-21).
# Run from repo root: bash scripts/archive_cycle_cardioid_resonance.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CYCLE="cycle_2026-07-21_cardioid_resonance"
ARCHIVE_DIR="archive/$CYCLE"
GITHUB_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
HF_SHA="${HF_SHA:-fe87388983ebdebb1f7304cdb6b7f843c17828ad}"

mkdir -p "$ARCHIVE_DIR"/{json_reports,figures,scripts,metadata,docs}

# === JSON reports from this cycle ===
cp -f outputs/cardioid_golden_angle_probe_20260721_*.json "$ARCHIVE_DIR/json_reports/" 2>/dev/null || true
cp -f outputs/cusp_resonance_probe_20260721_*.json     "$ARCHIVE_DIR/json_reports/" 2>/dev/null || true
cp -f outputs/pde_relaxation_probe_20260721_*.json     "$ARCHIVE_DIR/json_reports/" 2>/dev/null || true
cp -f outputs/cardioid_kappa_amp_sweep_20260721_*.json "$ARCHIVE_DIR/json_reports/" 2>/dev/null || true

# === Key figures (outputs + polished docs/figures) ===
for f in \
  cardioid_golden_angle_probe.png \
  cardioid_cusp_density.png \
  cardioid_three_way_star.png \
  cusp_resonance_probe.png \
  cardioid_kappa_amp_sweep.png \
  pde_cardioid_compare.png \
  pde_cardioid_compare_helical.png \
  pde_cardioid_compare_hopfion.png \
  pde_relaxation_probe.png \
  pde_relaxation_probe_helical.png \
  pde_relaxation_probe_hopfion.png
do
  [[ -f "outputs/$f" ]] && cp -f "outputs/$f" "$ARCHIVE_DIR/figures/"
  [[ -f "docs/figures/$f" ]] && cp -f "docs/figures/$f" "$ARCHIVE_DIR/figures/"
done
# Extra early-time helical compare if present
[[ -f docs/figures/pde_cardioid_compare_helical_nt50.png ]] && \
  cp -f docs/figures/pde_cardioid_compare_helical_nt50.png "$ARCHIVE_DIR/figures/"

# === New/updated scripts snapshot ===
cp -f scripts/cardioid_golden_angle_probe.py   "$ARCHIVE_DIR/scripts/"
cp -f scripts/cusp_resonance_probe.py          "$ARCHIVE_DIR/scripts/"
cp -f scripts/cardioid_kappa_amp_sweep.py      "$ARCHIVE_DIR/scripts/"
cp -f scripts/pde_relaxation_probe.py          "$ARCHIVE_DIR/scripts/"
cp -f scripts/archive_cycle_cardioid_resonance.sh "$ARCHIVE_DIR/scripts/" 2>/dev/null || true

# === Docs snapshot (HF + depth notes) ===
cp -f docs/CARDIOID_RESONANCE_HF.md  "$ARCHIVE_DIR/docs/" 2>/dev/null || true
cp -f notes/CARDIOID_RESONANCE.md    "$ARCHIVE_DIR/docs/" 2>/dev/null || true

# === Metadata ===
cat > "$ARCHIVE_DIR/metadata/deployment.txt" <<EOF
Cycle: Cardioid Resonance Layer
Date: 2026-07-21
Archived_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
GitHub SHA: ${GITHUB_SHA}
HF SHA: ${HF_SHA}
HF Space: https://huggingface.co/spaces/kinaar111/mystery
GitHub repo: https://github.com/kinaar8340/mystery

Key achievements:
- Cardioid modulation on golden-angle & 9/π stepping
- Explicit metrics (align_support, radial_collapse, burst_fraction, cusp_coherence)
- PDE envelope coupling (modulator, not generator)
- Structured IC tests (helical best responder)
- κ/A parameter sweeps
- Optimal amplitude note (A ≈ 0.7–0.8)
- HF Space documentation section (CARDIOID_RESONANCE_HF + demo_core HTML)

Reproduce:
  .venv/bin/python scripts/cardioid_golden_angle_probe.py
  .venv/bin/python scripts/cusp_resonance_probe.py
  .venv/bin/python scripts/cardioid_kappa_amp_sweep.py
  .venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid --ic helical --nt 50
  bash scripts/archive_cycle_cardioid_resonance.sh
EOF

# === Archive README ===
cat > "$ARCHIVE_DIR/README.md" <<'EOF'
# Cycle Archive: Cardioid Resonance Layer

**Date**: 2026-07-21  
**Status**: Ready for / deployed to HF Space (see `metadata/deployment.txt` for SHAs)

## Summary

This cycle added a full **resonance laboratory** layer on top of the existing gauged Hopf lattice work:

- Geometric probes using cardioid envelope on golden-angle stepping
- Quantifiable resonance metrics (explicit formulas)
- Dynamical coupling via PDE (optional cardioid envelope on non-diffusive drive)
- Structured initial-condition validation (uniform control, helical, hopfion)
- Comprehensive κ/A sweeps
- Optimal-amplitude note (burst peaks at A ≈ 0.7–0.8)

## Key Files

| Path | Contents |
|------|----------|
| `json_reports/` | All run outputs and metrics from 2026-07-21 |
| `figures/` | Polished visualization suite |
| `scripts/` | New and modified probe scripts (snapshot) |
| `docs/` | `CARDIOID_RESONANCE.md` + HF summary markdown |
| `metadata/deployment.txt` | SHAs, Space URL, reproduce commands |

## Main Outcomes

- Cardioid acts as a **modulator** of existing structure (strongest on helical ICs)
- Optimal burst amplification at **A ≈ 0.7–0.8** (over-collapse at A → 1)
- Helical seeds are the cleanest dynamical testbed; uniform IC is the negative control
- Cusp occupation is primarily early-time (~nt=50); longer-term benefit in σ and 369
- Full documentation and HF Space section completed

## Core Numbers (anchor)

| Metric | Value |
|--------|-------|
| Cusp pts (N=512, w=0.25) | 40, ρ ≈ 0.982 |
| align_support unit → cardioid | 0.50 → 0.72 |
| Burst raw → mod (A=0.5, κ_doc) | 0.074 → 0.199 |
| PDE helical Δσ / Δ369 (A=0.5, nt=50) | +0.013 / +0.015 |

## Deployment

See `metadata/deployment.txt` for current GitHub / HF SHAs and the Space URL:

https://huggingface.co/spaces/kinaar111/mystery

This archive preserves the state of the **July 21, 2026** Cardioid Resonance development cycle.
EOF

# Manifest
{
  echo "# Archive manifest"
  echo "path|bytes"
  find "$ARCHIVE_DIR" -type f | sort | while read -r f; do
    printf '%s|%s\n' "${f#$ARCHIVE_DIR/}" "$(wc -c < "$f" | tr -d ' ')"
  done
} > "$ARCHIVE_DIR/metadata/manifest.txt"

echo "Archive created at: $ARCHIVE_DIR"
echo "GitHub SHA: $GITHUB_SHA"
find "$ARCHIVE_DIR" -type f | wc -l | xargs echo "Files:"
du -sh "$ARCHIVE_DIR"
ls -lh "$ARCHIVE_DIR"
ls -lh "$ARCHIVE_DIR"/*
