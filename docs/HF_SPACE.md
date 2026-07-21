# Hugging Face Space — deploy & sync

Live demo: [huggingface.co/spaces/kinaar111/mystery](https://huggingface.co/spaces/kinaar111/mystery)

Source bundle: `space/mystery/` (Gradio 5.12.0, Python 3.12)

---

## Repositories

| Remote | URL | Role |
|--------|-----|------|
| **GitHub** (research) | [github.com/kinaar8340/mystery](https://github.com/kinaar8340/mystery) | Probes, notes, figures, Space source |
| **HF Space** (runtime) | [huggingface.co/spaces/kinaar111/mystery](https://huggingface.co/spaces/kinaar111/mystery) | Public Gradio app |

GitHub is the canonical source. The HF Space repo is a deployment target — updated by rsync, not a fork you edit by hand.

---

## One-command deploy

From the repo root:

```bash
bash scripts/deploy_hf_space.sh
```

This runs, in order:

1. **`scripts/sync_hf_space.sh`** — refresh `space/mystery/build_info.py`, `requirements.txt`, and the HF-facing `README.md` template
2. **Git commit + push** to `origin main` on GitHub (`kinaar8340/mystery`)
3. **Clone HF Space** via SSH (`git@hf.co:spaces/kinaar111/mystery`)
4. **rsync** `space/mystery/` → HF clone (excludes `.git`, `.venv`, `__pycache__`)
5. **Git commit + push** on the HF Space repo (if there are changes)

Requires:

- SSH key authorized for GitHub and Hugging Face
- HF Space already created (Gradio SDK, name `mystery`, owner `kinaar111`)

---

## Sync only (no git push)

To refresh the local bundle without deploying:

```bash
bash scripts/sync_hf_space.sh
```

Writes:

| File | Purpose |
|------|---------|
| `space/mystery/build_info.py` | `BUILD_COMMIT`, `BUILD_UPDATED_UTC` for the in-app terminal |
| `space/mystery/requirements.txt` | Pinned Space dependencies |
| `space/mystery/README.md` | HF Space card (YAML front matter + markdown) |

**Do not edit `space/mystery/README.md` by hand** — change the template in `scripts/sync_hf_space.sh` and re-run sync.

---

## Space layout

```
space/mystery/
├── app.py          # Gradio UI (Gravity, Presets, README, Figures)
├── demo_core.py    # φ-e-π metrics, unit-cell 3D plot, deformation MP4 renderer
├── build_info.py   # Auto-generated build stamp
├── requirements.txt
└── README.md       # Auto-generated HF card
```

Cover image is served from GitHub raw (`mystery_image.png` at repo root) — HF git rejects large binaries without Xet.

---

## UI tabs (Space)

| Tab | Contents |
|-----|----------|
| **Gravity** (default) | Two-column unit-cell explorer — presets, TUI metrics, deformation animation |
| **Presets** | Nine-slot preset grid with per-preset metrics and edit drawer |
| **README** | In-app project summary |
| **Figures** | Reference plots from the probe suite (includes cardioid / cusp resonance) |

**Cardioid Resonance** (repo + README section + Figures): golden-angle × cardioid
cusp probes, κ/A sweeps, PDE helical compare. In-app HTML:
`build_cardioid_resonance_html()` in `demo_core.py`. Markdown source:
`docs/CARDIOID_RESONANCE_HF.md` · depth: `notes/CARDIOID_RESONANCE.md`.
Live full suite is local via `run_all.py` (includes `cardioid_kappa_amp_sweep.py`).

**Demo J — Brackish Heartbeat** (Gravity tab, demo row): interactive dashboard
(gauged hour/minute/∫wind clock, wind-synced nested Platonic solids, live
divergence strip). Sliders + presets (Calm Sea, Building Storm, etc.) and
**Loop Animation** for MP4 export. See `notes/brackish_dynamics.md`.

### Gravity tab layout

**Left column**

- **QUICK PRESETs** — 8 keypad slots + **Animate deformation** toggle
- **Preset Metrics TUI** — serial-style status + live parameter snapshot
- **Parameter levels** (collapsed) — bar-graph dial readout
- **Manual Edit** (collapsed) — latch to unlock sliders

**Right column**

- **Unit Cell Viewport** — static Plotly 3D plot, or looping MP4 when animation is active

### Preset slots

| Button | Slot | Profile |
|--------|------|---------|
| 1 | 0 | Parameter catalog (menu) |
| 2 | 1 | Rigid cube (pressure 0, δ_z 0) |
| 3 | 2 | Full π bowl + φ/e concave pinch |
| 4 | 3 | Full π bowl |
| 5 | 4 | φ/e concave pinch |
| 6–8 | 5–7 | Reserved — keeps current manual dial values |

**Animate deformation** — first click renders a server-side looping MP4 (`demo_core.render_unit_cell_deformation_video`); second click stops and restores the static plot.

**Manual Edit** — matrix-green latch; sliders are locked until enabled.

---

## Local dev (Space)

```bash
cd space/mystery
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Gradio serves on port 7860 by default.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| HF clone fails | Create Space at [huggingface.co/new-space](https://huggingface.co/new-space) (Gradio, `kinaar111/mystery`) or `hf repo create mystery --type space --space_sdk gradio` |
| Stale HF README | Re-run `sync_hf_space.sh` — README is generated, not hand-edited |
| Video encode error | libx264 needs even dimensions — handled by `_ensure_even_frame` in `demo_core.py` |
| Build stamp missing | Run sync before local `app.py` — imports `build_info.py` at runtime |

---

## Related

- Root README: [../README.md](../README.md)
- Probe results: [RESULTS.md](RESULTS.md)
- Repo index: [../references/github_repos.md](../references/github_repos.md)