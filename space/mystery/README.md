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
short_description: φ²+e²≈π² — Gravity unit-cell presets + Live Probe
---

# Mystery — φ, e, π Emergent Signature

<p align="center">
  <img src="https://raw.githubusercontent.com/kinaar8340/mystery/main/mystery_image.png" alt="Mystery cover" width="100%" style="max-width: 720px; border-radius: 12px;" />
</p>

**Browser demo** of the Mystery research notebook: near-Pythagorean triangle φ²+e²≈π², holonomy-gap scaling B(κ), unit-cell deformation, and 30-60-90 / 3-6-9 comparisons.

Opens on the **Gravity** tab — two-column preset explorer with live TUI metrics and optional deformation animation. **Live Probe** keeps the κ slider, triangle plots, and matrix terminal from [orbital-braille-vqc](https://huggingface.co/spaces/kinaar111/orbital-braille-vqc).

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

## Live Probe tab

1. Tune **κ** (κ_doc = 0.85 marked).
2. Click **Run analysis** → metrics + triangle / κ-sweep plots.
3. Use the **matrix terminal** and keypad for build info and help.
4. **Figures** tab — reference plots from the probe suite.

---

## Key results

| Quantity | Value |
|----------|-------|
| R = φ²+e²−π² | **+0.137486** (~1.39% error) |
| Angles | **31.0° / 59.9° / 89.1°** |
| 3-6-9 tens | **3.10 / 5.99 / 8.91** |
| κ* = e/π − R/π² | **≈ 0.8513** (0.16% from κ_doc) |

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
