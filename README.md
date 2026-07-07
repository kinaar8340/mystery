<p align="center">
  <img src="mystery_image.png" alt="Mystery — maple leaf on a Roman-numeral clock with glowing green geometric overlay, autumn leaves, and cosmic background; nature, time, and topology" width="100%" style="max-width: 820px; border-radius: 12px;" />
</p>

# Mystery — φ, e, π Emergent Signature

[![Repository](https://img.shields.io/badge/GitHub-mystery-blue)](https://github.com/kinaar8340/mystery)
[![Parent TOE](https://img.shields.io/badge/TOE-kinaar8340%2Ftoe-lightgrey)](https://github.com/kinaar8340/toe)

Quantified research notebook exploring the near-Pythagorean triangle formed by φ, e, and π — and how that numerical harmony relates to vortex-math 3-6-9 positional geometry and the gauged Hopf lattice TOE.

**Status:** Compatible emergent signature — not an exact identity, not forced by invariants, not contradicted by simulation.

**Project stage:** Early research notebook (June 2026). The [Hugging Face Space](https://huggingface.co/spaces/kinaar111/mystery) opens on the **Gravity** tab with **Presets**, **README**, and **Figures** tabs. Full probe depth, derivations, and JSON outputs live in this repo.

## Overview

Mystery is a computational framework for studying **dynamical emergence** in gauged Hopf lattice systems. It explores whether a topological model with twisting and relaxation dynamics can evolve toward stable states that align with specific mathematical relations, particularly the near-Pythagorean relation φ² + e² ≈ π².

The framework implements a multi-stage optimization method (the **Analog Objective**) that guides the system toward high-performing configurations. Key results include:

- Consistent convergence to robust attractor states with high hybrid scores (~0.9990)
- Clear separation between documented and simulation-optimized parameters
- Strong robustness of survival alignment under parameter variation and different initial conditions

A notable aspect of the work is the **dual role** assigned to the gauge parameter κ:

| Symbol | Value | Role |
|--------|-------|------|
| **κ_doc** | 0.85 | Theoretical anchor for documentation and residual scaling relations |
| **κ_sim** | ≈ 0.89 | Practical optimum for meta-optimization and dynamical alignment at λt = 2 |
| **κ\*** | ≈ 0.8513 | Exact value that nulls the residual in the scaling expression |

An interactive visualization layer is available on [Hugging Face Spaces](https://huggingface.co/spaces/kinaar111/mystery), allowing direct exploration of the model's behavior and tuning process.

While the broader physical implications remain speculative, the project offers a reproducible methodology for investigating how mathematical signatures can arise from the dynamics of complex geometric systems.

---

## Results at a glance

| Probe | Key finding |
|-------|-------------|
| `phi_e_pi_analysis` | R = **+0.137486** (1.39% error); angles **31.0° / 59.9° / 89.1°** |
| `hopf_constant_bridge` | W_g = **111.408**; **κ_doc = 0.85** vs e/π **0.865** (Δ 1.76%); **κ_sim ≈ 0.89** (production); Θ_link ≈ π, θ_crit ≈ **5.81** |
| `vortex_369_clock` | Angles ÷10° → **3.10 / 5.99 / 8.91** (nearest 3/6/9) |
| `residual_bound_probe` | Best near-miss: **π²(e/π−κ) ≈ 0.151** (9.5% from R) |
| `residual_kappa_sweep` | **κ* = e/π − R/π² ≈ 0.8513** — only **0.15%** from κ_doc |
| `pde_relaxation_probe` | Uniform IC → ⟨θ⟩≈0.084, **σ=0** (expected dissipative minimum) |
| `pde_structured_ic_probe` | Hopfion/helical seeds retain **σ>0** and finite-k FFT structure |
| `conduit_angular_probe` | **~8% / ~6% / ~4%** within 5° of 30°/60°/90° (not forced) |
| `meta_optimize_phi_probe` | κ=**0.85**, φ_b≈**0.754**, W_g≈**111.89** — not e/π or φ⁻¹ |
| `rodin_hopf_fiber_map` | Doubling cycle **1-2-4-8-7-5** mapped to S¹ phase increments |

Full table: [`docs/RESULTS.md`](docs/RESULTS.md) · Scaling note: [`notes/residual_scaling.md`](notes/residual_scaling.md)

### Dual-role κ

The model exhibits a mild but consistent preference: while the documented gauge value is **κ_doc = 0.85**, systematic tuning and survival alignment at λt = 2 converge near **κ_sim ≈ 0.89**. We maintain both with clearly separated roles.

| Symbol | Value | Role |
|--------|-------|------|
| **κ_doc** | 0.85 | Documentation / theory (θ_crit, B(κ), residual framing) |
| **κ_sim** | ≈ 0.89 | Simulation / production (Stage 6 dual-analog optimum) |
| **κ\*** | ≈ 0.8513 | Exact null e/π − R/π² |

Production runs use κ_sim; formulas and the HF κ slider default retain κ_doc. Physical interpretation of the ~4% shift: [`notes/kappa_sim_interpretation.md`](notes/kappa_sim_interpretation.md). Details: [`docs/RESULTS.md`](docs/RESULTS.md) · [`notes/stage6_analog_tuning.md`](notes/stage6_analog_tuning.md).

---

## Emergent Residual Analogs: Golden Angle & Exponential Survival (e⁻²)

The Pythagorean residual

```
R = φ² + e² − π² ≈ +0.137486   (~1.39% relative error on π²)
```

is not treated as a numerical mistake. Two independent dynamical analogs sit within ~1–2% of R and offer complementary interpretive lenses inside the gauged Hopf lattice / conduit / PDE framework ([toe](https://github.com/kinaar8340/toe)).

### Golden-angle proportion (~0.1375)

| Quantity | Value | Δ from R |
|----------|-------|----------|
| 137.5° / 1000 | **0.1375** | ~0.07% |
| Golden angle 360°(1 − φ⁻¹) | **137.51°** | — |
| Related packing scale φ⁻² | **0.3820** | (conceptual link to irrational rotation) |

**Dynamical meaning:** The golden angle is the optimal irrational rotational increment for dense, non-repeating coverage (phyllotaxis-style self-organization). It connects naturally to:

- Hopf-fiber twisting and unit-circle phase walks on \(S^1\)
- Rigid-cube + axial unit-circle presets in the [HF Space Gravity tab](https://huggingface.co/spaces/kinaar111/mystery)
- Rotational efficiency in conduit helix geometry (`twist_rate`, toroidal modulo-9 wrap)

This analog addresses **how** residual structure may persist in angular packing — not **whether** \(R\) is an exact identity.

### Exponential survival e⁻² (~0.1353)

| Quantity | Value | Δ from R |
|----------|-------|----------|
| e⁻² | **0.135335** | **~1.57%** |
| R = φ² + e² − π² | **0.137486** | — |

**Dynamical meaning:** In any memoryless constant-rate process `f(t) = f₀·e^(−λt)`, the universal **survival fraction** after exactly two characteristic times (λt = 2) is e⁻². This is the broadest "residual after normalized dynamics" — theory-agnostic and already tied to the e² term inside R.

In the TOE twist-PDE and conduit gauge dynamics, the mean-field restoring torque `−κθ̄` identifies an effective rate λ ≈ κ. Documentation uses **κ_doc = 0.85**; tuned production runs converge to **κ_sim ≈ 0.89**. Normalizing simulation time to λt = 2 therefore tests whether measured survival fractions (mean twist, fluctuation energy, braiding phase residuals, identity persistence) track e⁻² or the observed R.

**Connections to existing probes:**

| Element | Role |
|---------|------|
| `pde_relaxation_probe` / `pde_relaxation.py` | Dissipative relaxation; uniform IC → low-twist minimum; structured IC retains \(\sigma > 0\) |
| `RubikConeConduit` gauge damping | Global pointer \(\kappa\); \(W_g \approx 111.408\); braiding \(\approx 0.814\) |
| `hopf_constant_bridge` | Holonomy gap e/π − κ; B(κ) = π²(e/π − κ) scaling |
| `conduit_angular_probe` | Angular distributions near 30°/60°/90° (modest, not forced) |
| Attractors / meta_optimize | κ_doc = 0.85 (docs); κ_sim ≈ 0.89 (production); transcendentals are not optima |

**Complementarity:** Golden angle → **rotational packing efficiency**; e⁻² → **temporal persistence after scaled relaxation**. Together they strengthen the reading of R as a **compatible emergent signature** in a geometric-dynamical system with both twist and decay — not as a fitting error.

### Proposed Experiments

1. **λt = 2 normalization (implemented):** Run PDE and gauged-twist evolution with `normalize_to_lambda_t=2`; compare mean survival, fluctuation survival, and invariant residuals to e⁻², R, and golden-angle fraction.
   ```bash
   python scripts/exponential_survival_probe.py
   python ../toe/scripts/pde_relaxation.py --normalize-to-lambda-t 2
   ```
2. **Golden-angle twist increments (Stage 3):** Step helix / rigid-cube rotation by 137.5078° or fractional φ⁻²; measure angular histogram shift vs `conduit_angular_probe` baseline.
3. **Combined analog sweep (Stage 4):** Vary `twist_rate`, IC structure, and normalization jointly; quantify which analog (or pair) best aligns W_g, κ, and braiding residuals.
4. **Cross-link PDE ↔ conduit:** Correlate PDE mean_survival at λt = 2 with conduit `identity_residual` and `braiding_residual` from `run_survival_probe`.

See [`notes/emergent_signatures.md`](notes/emergent_signatures.md) and toe [`relaxation_survival.py`](../toe/src/relaxation_survival.py) for implementation details.

### Holonomy-gap scaling (standout)

At **κ* = e/π − R/π² ≈ 0.8513**, the scaling B(κ) = π²(e/π−κ) exactly nulls R. Documented **κ = 0.85** is only **0.16%** away — but B(κ_doc) is still **9.5%** above R. κ* is not claimed as the physical value; its proximity to the locked invariant is the observation.

![κ sweep](docs/figures/residual_kappa_sweep.png)

---

## Assessment (June 2026)

Four probes move this project from exploratory numerology into a **well-quantified compatible emergent signature** within the gauged Hopf lattice framework:

| Probe | Result |
|-------|--------|
| **Residual** | R = φ²+e²−π² = **+0.137486** (stable, drift &lt; 1e−10) |
| **Meta-optimizer** | κ_doc = **0.85**; κ_sim ≈ **0.89** (dual-analog); W_g ≈ **111.41**; φ_b ≈ **0.754** — transcendentals are **not** attractors |
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

## Hugging Face Space

| Resource | URL |
|----------|-----|
| Live demo | [huggingface.co/spaces/kinaar111/mystery](https://huggingface.co/spaces/kinaar111/mystery) |
| Deploy guide | [`docs/HF_SPACE.md`](docs/HF_SPACE.md) |

**Gravity tab (default):** two-column layout — QUICK PRESETs (catalog + rigid cube + bowl/pinch variants), Preset Metrics TUI, optional deformation MP4, Manual Edit latch for sliders.

**Deploy** (sync bundle → GitHub push → HF rsync):

```bash
bash scripts/deploy_hf_space.sh
```

Sync only: `bash scripts/sync_hf_space.sh`

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
| `scripts/deploy_hf_space.sh` | Sync → GitHub commit/push → HF Space rsync/deploy |
| `scripts/sync_hf_space.sh` | Regenerate `space/mystery/` bundle (build_info, requirements, HF README) |
| `phi_e_pi_analysis.py` | High-precision φ²+e²≈π², triangle angles, 30-60-90 comparison |
| `hopf_constant_bridge.py` | κ, W_g, θ_crit, φ_b vs e/π and transcendental ratios |
| `vortex_369_clock.py` | 3-6-9 positional geometry, Rodin mod-9, clock dial |
| `residual_bound_probe.py` | Bound R via W_g, κ; Kepler triangle contrast |
| `pde_relaxation_probe.py` | Meta-seeded PDE + FFT/correlation analysis |
| `conduit_angular_probe.py` | 30°/60°/90° separations with `vortex_math_369` |
| `conduit_probe.py` | TOE conduit invariant smoke test |
| `meta_optimize_phi_probe.py` | Meta-optimizer + optional survival/golden objective (Stage 6) |
| `residual_kappa_sweep.py` | R vs π²(e/π−κ) sweep; κ* null point |
| `pde_structured_ic_probe.py` | Hopfion + two-gyro helical PDE seeds |
| `exponential_survival_probe.py` | λt = 2 normalization; survival vs e⁻², R, golden angle |
| `kappa_survival_sweep.py` | κ ∈ [0.80, 0.90] mean_survival @ λt=2 |
| `golden_angle_twist_probe.py` | Golden helix steps + S¹ phase histograms |
| `analog_comparative_sweep.py` | Grid: IC × twist_rate × λt × step_mode |
| `analog_cross_analysis.py` | Stage 5 overlay figure (κ sweep + sweep scatter) |
| `rodin_hopf_fiber_map.py` | Rodin mod-9 doubling → Hopf fiber phases |

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
| [`docs/HF_SPACE.md`](docs/HF_SPACE.md) | Git + HF deploy workflow, Gravity tab layout, preset slots |
| [`notes/angle_derivation.md`](notes/angle_derivation.md) | Step-by-step law-of-cosines angles; 369 tens; interpretive vs computed |
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

1. **λt = 2 + golden-angle sweeps** — `exponential_survival_probe.py` baseline; Stage 3–4 twist increments at 137.5°
2. **Extend structured PDE** — longer runs, higher resolution; correlate FFT peaks with φ/e/π at scale
3. **Derive residual bound** — formal Skyrme + holonomy reduction for B(κ) = π²(e/π−κ)
4. **Falsify Rodin map** — match doubling-step ΔΘ to burst-reset events in lattice sims
5. **Island-bake conduit** — 369 flags with `epoch_bake_sweep` configurations

---

## License

Research notebook and analysis scripts: **CC-BY-NC-SA-4.0**. Upstream TOE/VQC/HFB code retains its respective licenses.