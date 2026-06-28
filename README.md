# Mystery — φ, e, π Emergent Signature

[![Repository](https://img.shields.io/badge/GitHub-mystery-blue)](https://github.com/kinaar8340/mystery)
[![Parent TOE](https://img.shields.io/badge/TOE-kinaar8340%2Ftoe-lightgrey)](https://github.com/kinaar8340/toe)

Quantified research notebook exploring the near-Pythagorean triangle formed by φ, e, and π — and how that numerical harmony relates to vortex-math 3-6-9 positional geometry and the gauged Hopf lattice TOE.

**Status:** Compatible emergent signature — not an exact identity, not forced by invariants, not contradicted by simulation.

---

## Assessment (June 2026)

Four probes move this project from exploratory numerology into a **well-quantified compatible emergent signature** within the gauged Hopf lattice framework:

| Probe | Result |
|-------|--------|
| **Residual** | R = φ²+e²−π² = **+0.137486** (stable, drift &lt; 1e−10) |
| **Meta-optimizer** | κ = **0.8500** exactly; W_g ≈ **111.89**; φ_b ≈ **0.754** — transcendentals are **not** attractors |
| **PDE relaxation** | Uniform low-twist minimum; DC-dominated FFT — **expected**, not a failure |
| **Conduit angular** | ~8% near 30° / ~6% near 60° / ~4% near 90° — modest, not a 3-6-9 lock |

**Leading algebraic near-miss:** π²(e/π − κ) ≈ 0.151 (~9.5% from R). Hints the residual may scale with the **holonomy gap** in the effective low-energy Skyrme reduction — promising, not yet derived.

Full write-up: [`notes/emergent_signatures.md`](notes/emergent_signatures.md)

---

## Figures

| φ-e-π triangle vs 30-60-90 | PDE relaxation (θ slice + FFT) |
|:---:|:---:|
| ![φ-e-π triangle](docs/figures/phi_e_pi_triangle.png) | ![PDE probe](docs/figures/pde_relaxation_probe.png) |

| Conduit angular histograms | Vortex 3-6-9 / clock geometry |
|:---:|:---:|
| ![Conduit angular](docs/figures/conduit_angular_histogram.png) | ![369 clock](docs/figures/vortex_369_clock.png) |

Regenerate: `python run_all.py` → `outputs/`

---

## Quick start

```bash
git clone https://github.com/kinaar8340/mystery.git && cd mystery
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py
```

**TOE-linked probes** (conduit, meta-optimizer) use `~/Projects/toe/venv` when present. Clone [toe](https://github.com/kinaar8340/toe) alongside for full stack:

```bash
# Optional: full conduit + meta-optimizer probes
cd ../toe && python3 -m venv venv && venv/bin/pip install torch optuna pydantic matplotlib
cd ../mystery && .venv/bin/python run_all.py
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `phi_e_pi_analysis.py` | High-precision φ²+e²≈π², triangle angles, 30-60-90 comparison |
| `hopf_constant_bridge.py` | κ, W_g, θ_crit, φ_b vs e/π and transcendental ratios |
| `vortex_369_clock.py` | 3-6-9 positional geometry, Rodin mod-9, clock dial |
| `residual_bound_probe.py` | Bound R via W_g, κ; Kepler triangle contrast |
| `pde_relaxation_probe.py` | Meta-seeded PDE + FFT/correlation analysis |
| `conduit_angular_probe.py` | 30°/60°/90° separations with `vortex_math_369` |
| `conduit_probe.py` | TOE conduit invariant smoke test |
| `meta_optimize_phi_probe.py` | Meta-optimizer + φ/e/π clustering |

---

## Core claim (not a proof)

There is **no known closed-form identity** φ² + e² = π²:

```
φ² + e² − π² ≈ +0.1375   (~1.39% relative Pythagorean error)
```

Triangle angles: φ→31.0°, e→59.9°, π→89.1° — near 30-60-90, not exact. The **Kepler triangle** (1:√φ:φ) is exact within golden geometry; φ-e-π mixes three transcendental families and stays approximate.

---

## Documentation

| Doc | Contents |
|-----|----------|
| [`notes/emergent_signatures.md`](notes/emergent_signatures.md) | Probe results and overall assessment |
| [`notes/synthesis.md`](notes/synthesis.md) | Original thought-experiment synthesis |
| [`notes/open_questions.md`](notes/open_questions.md) | Resolved items + prioritized next moves |
| [`notes/theta_crit_reconciliation.md`](notes/theta_crit_reconciliation.md) | Dual burst-threshold resolution |
| [`references/local_paths.md`](references/local_paths.md) | Local TOE/VQC/HFB file index |
| [`references/github_repos.md`](references/github_repos.md) | Related kinaar8340 repositories |

---

## Related repositories

| Repo | Role |
|------|------|
| [toe](https://github.com/kinaar8340/toe) | Gauged Hopf lattice, flux flywheels, conduit PDE |
| [vqc_proto](https://github.com/kinaar8340/vqc_proto) | Orbital Braille — helical OAM, quaternion codec |
| [hfb](https://github.com/kinaar8340/hfb) | Hopf Flux Bubble — topological defects |

---

## Prioritized next moves

1. **Structured PDE initial conditions** — seed Hopfions / flux-flywheel twists; hunt FFT peaks near φ/e/π scales
2. **Formal residual bound** — derive R ≈ π²(e/π−κ) in Skyrme + holonomy effective reduction
3. **Rodin cycle ↔ S³ fiber phase** — map mod-9 doubling onto Hopf fiber increments
4. **Longer conduit runs** — 369 flags + island-bake configurations

---

## License

Research notebook and analysis scripts: **CC-BY-NC-SA-4.0**. Upstream TOE/VQC/HFB code retains its respective licenses.