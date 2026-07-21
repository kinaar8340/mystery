# Cardioid Resonance

**Resonance laboratory** layer on the gauged Hopf lattice: golden-angle packing + cardioid envelope + cusp / burst diagnostics + \(350/\pi\) scale. Math and observation stay explicit; interpretation is optional.

Full note: [`notes/CARDIOID_RESONANCE.md`](https://github.com/kinaar8340/mystery/blob/main/notes/CARDIOID_RESONANCE.md) · Scripts: `cardioid_golden_angle_probe.py`, `cusp_resonance_probe.py`, `cardioid_kappa_amp_sweep.py`, `pde_relaxation_probe.py --compare-cardioid`.

---

## Framing (three layers)

| Layer | Content |
|-------|---------|
| **Mathematical** | \(r=1+\cos\theta\); \(\theta_g=2\pi/\varphi^2\); cusp at \(\theta=\pi\); \(\theta_\mathrm{crit}=\pi(1+\kappa)\) |
| **Observational** | Cusp density \(\rho\), align_support, radial_collapse, burst_fraction, κ/A sweeps, PDE helical |
| **Interpretive** | Optional only — cusp as burst/alignment proxy; golden path as efficient packing |

**Separation:** `align_support` rises from **cardioid-body** weighting at φ-e-π angles; `radial_collapse` and `burst_fraction` capture the **cusp singularity**. Angular \(\rho\approx 1\) (no pile-up).

---

## Core geometric results (N=512, κ=0.85)

| System | Cusp pts | ρ | align_support | radial_collapse |
|--------|----------|---|---------------|-----------------|
| Golden (unit r) | 40 | ≈0.982 | **0.500** | 1.00 |
| Golden + cardioid | 40 | ≈0.982 | **0.724** | ≫1 (full A≈1) |
| 9/π + cardioid | 42 | ≈1.03 | elevated | ≫1 |

| Dynamical probe (A=0.5) | Value |
|-------------------------|--------|
| Burst fraction raw → mod | **0.074 → 0.199** (Δ **+0.125**) |
| Radial collapse (amp envelope) | **≈2.07** |
| Best geometric scale coherence | \(N\approx 2\times 350/\pi\) (≈223) |
| Best dynamical scale coherence | \(N\approx 350/\pi\) (≈111) |

Different observables peak at different multiples of \(350/\pi\) — the accumulation scale interacts with the diagnostic.

---

## κ / A sweeps (A=0.5 for κ; κ_doc for A)

### Geometric anchors @ A = 0.5

| κ | Role | burst raw | burst mod | Δ burst | collapse | align |
|---|------|-----------|-----------|---------|----------|-------|
| **0.85** | κ_doc | 0.074 | **0.199** | **+0.125** | 2.07 | 0.91 |
| **≈0.89** | κ_sim | 0.055 | **0.195** | **+0.141** | 2.07 | 0.91 |
| **≈0.851** | κ* | (nearest grid ≈ κ_doc) | — | — | — | — |

Collapse and align are nearly **κ-flat** at fixed A (radial geometry). Burst fraction tracks \(\theta_\mathrm{crit}=\pi(1+\kappa)\).

### Burst & collapse vs A @ κ_doc = 0.85

| A | burst mod | Δ burst | collapse | align |
|---|-----------|---------|----------|-------|
| 0.0 | 0.074 | 0 | 1.00 | 0.77 |
| 0.3 | 0.176 | +0.10 | 1.46 | 0.85 |
| **0.5** | **0.199** | **+0.125** | **2.07** | **0.91** |
| 0.7 | 0.207 | +0.13 | 3.46 | 0.96 |
| 1.0 | 0.168 | +0.09 | ≫1 | 1.04 |

### Optimal amplitude

Geometric **burst amplification peaks at A ≈ 0.7–0.8**. Higher amplitudes increase radial collapse dramatically but can **reduce net burst gain** due to over-focusing at the cusp (r → 0; holonomy proxy / sampling saturation). Documented operating point **A = 0.5** sits on the rising flank: strong collapse (~2×) and solid Δburst (+0.125) without the A→1 over-collapse regime.

### PDE helical (early nt=50) — modulator test

| Setting | Δσ (mod−raw) | Δ frac_369 | cusp_frac |
|---------|--------------|------------|-----------|
| κ=0.85, A=0.5 | **+0.013** | **+0.015** | 0.08 (retained) |
| κ=0.89, A=0.5 | +0.014 | −0.005 | 0.08 |
| κ=0.85, A=0.0 → 1.0 | 0 → **+0.026** | 0 → **+0.045** | 0.08 → 0.105 |

**Uniform IC** remains the negative control (cardioid only accelerates damping). **Helical IC** shows the positive modulator response: higher residual variance and mild 3-6-9 lift under increasing A. **Hopfion** is less responsive (weaker initial angular variation / cusp occupation).

**Early vs late:** Cusp occupation is primarily an **early-time** feature (~present at nt=50, emptied by ~nt=100 in both baseline and modulated runs). Longer-term cardioid benefit under dissipation appears in **σ** and **369**, not late-time cusp_frac.

---

## Metric formulas (math layer)

```
θ_k = k · θ_step  (mod 2π)     θ_g = 2π/φ²
r(θ) = 1 + cos(θ)              cusp @ θ = π

ρ = f_cusp / (w/π)             f_cusp = (# |θ−π|≤w)/N

align_support = mean_α [ (Σ w_k r_k)/(Σ w_k)/2 ]
  w_k = exp(−½ dist(θ_k,α)² / σ²)

radial_collapse = mean(r|bulk) / mean(r|cusp)

burst_fraction = mean( holonomy > θ_crit )
  holonomy = (a·θ) mod 2π(1+κ),  a = 1+A cos θ
  θ_crit = π(1+κ)
```

---

## Figures

| Figure | Description |
|--------|-------------|
| [Three-way star](https://github.com/kinaar8340/mystery/blob/main/docs/figures/cardioid_three_way_star.png) | Unit golden \| golden+cardioid \| 9/π+cardioid + r-distribution inset |
| [Full probe panel](https://github.com/kinaar8340/mystery/blob/main/docs/figures/cardioid_golden_angle_probe.png) | Metrics + angular density + 350/π scale |
| [Cusp resonance](https://github.com/kinaar8340/mystery/blob/main/docs/figures/cusp_resonance_probe.png) | Burst mask, κ, scale, FFT |
| [κ/A sweeps](https://github.com/kinaar8340/mystery/blob/main/docs/figures/cardioid_kappa_amp_sweep.png) | Burst/collapse/align + PDE Δσ + grid |
| [PDE helical compare](https://github.com/kinaar8340/mystery/blob/main/docs/figures/pde_cardioid_compare_helical.png) | Structured IC cardioid vs baseline |

---

## Reproduce (local)

```bash
cd mystery
.venv/bin/python scripts/cardioid_golden_angle_probe.py
.venv/bin/python scripts/cusp_resonance_probe.py
.venv/bin/python scripts/cardioid_kappa_amp_sweep.py
.venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid --ic helical --nt 50
```

**Status:** Compatible emergent / resonant-geometry diagnostics — not an exact identity, not forced by invariants.
