---
title: Mystery — φ e π Emergent Signature
emoji: 🔮
colorFrom: green
colorTo: purple
sdk: gradio
sdk_version: 5.12.0
python_version: 3.12
app_file: app.py
pinned: false
license: mit
short_description: φ²+e²≈π² — Gravity unit-cell presets & figures
---

# Mystery — φ, e, π Emergent Signature

<p align="center">
  <img src="https://raw.githubusercontent.com/kinaar8340/mystery/main/bg1_mystery.png" alt="Mystery cover" width="100%" style="max-width: 720px; border-radius: 12px;" />
</p>

**Interactive computational laboratory** for dynamical emergence in gauged Hopf lattice systems — near-Pythagorean triangle φ²+e²≈π², Analog Objective tuning, holonomy-gap scaling B(κ), unit-cell deformation, and 30-60-90 / 3-6-9 comparisons.

Opens on the **Gravity** tab — two-column preset explorer with live TUI metrics and optional deformation animation. **README** tab includes **About this Project** (dual-role κ: κ_doc / κ_sim / κ*). **Figures** tab shows reference plots from the probe suite.

> Full 11-probe suite runs locally: [`run_all.py`](https://github.com/kinaar8340/mystery)

---

## Gravity tab (default)

**Left:** QUICK PRESETs (1 = catalog · 2 = rigid cube · 3–5 = bowl/pinch variants) · Preset Metrics TUI · Parameter levels · Manual Edit latch

**Right:** Unit Cell Viewport — 3D plot or looping deformation MP4 (**Animate deformation** toggle)

| Preset | Profile |
|--------|---------|
| 1 | Parameter catalog |
| 2 | Rigid cube |
| 3 | Full π bowl + φ/e concave pinch |
| 4 | Full π bowl |
| 5 | φ/e concave pinch |

---

## Other tabs

| Tab | Contents |
|-----|----------|
| **Presets** | Nine-slot preset grid with per-preset metrics and edit drawer |
| **README** | In-app project summary and probe hooks |
| **Figures** | φ-e-π triangle, κ sweep, 3-6-9 clock, Conduit angular histograms |

---

## Key results

| Quantity | Value |
|----------|-------|
| R = φ²+e²−π² | **+0.137486** (~1.39% error) |
| Angles | **31.0° / 59.9° / 89.1°** |
| 3-6-9 tens | **3.10 / 5.99 / 8.91** |
| κ* = e/π − R/π² | **≈ 0.8513** (0.16% from κ_doc) |

### Stage 6 — analog objective tuning (w_s=5, 30 trials)

| Mode | Loss | κ | mean_survival | Δ% vs R | hybrid |
|------|------|---|---------------|---------|--------|
| baseline | 57.22 | 0.89 | — | — | — |
| survival_penalty | 57.26 | 0.89 | 0.137651 | 0.121% | 0.9990 |
| dual_analog | **56.98** | 0.89 | 0.137651 | 0.121% | 0.9990 |

**50-trial confirmed** · robust across 18 grid points @ κ=0.89. Full tables: [docs/RESULTS.md](https://github.com/kinaar8340/mystery/blob/main/docs/RESULTS.md) · in-app under **Manual Edit → Stage 6 — Current Best & Robustness**.

**Framing:** compatible emergent signature within the gauged Hopf lattice TOE — not a derived identity.

---

## Links

| Resource | URL |
|----------|-----|
| Mystery repo | [github.com/kinaar8340/mystery](https://github.com/kinaar8340/mystery) |
| Deploy guide | [docs/HF_SPACE.md](https://github.com/kinaar8340/mystery/blob/main/docs/HF_SPACE.md) |
| TOE parent | [github.com/kinaar8340/toe](https://github.com/kinaar8340/toe) |
| UI template | [orbital-braille-vqc](https://huggingface.co/spaces/kinaar111/orbital-braille-vqc) |

Synced from `space/mystery/` via `scripts/sync_hf_space.sh`.
