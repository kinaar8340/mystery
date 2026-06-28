# Results at a Glance

Confirmed numbers from the latest clean `run_all.py` execution (June 2026).  
Regenerate JSON: `python run_all.py` → `outputs/`.

## Numerical core

| Quantity | Value |
|----------|-------|
| R = φ² + e² − π² | **+0.1374856866** |
| Relative Pythagorean error | **1.3930%** |
| Triangle angles (φ / e / π) | **30.996° / 59.900° / 89.104°** |
| Mean ratio deviation from 30-60-90 | **1.98%** |
| Angles ÷ 10° (3-6-9 tens) | **3.10 / 5.99 / 8.91** |

## Hopf lattice bridge

| Quantity | Value |
|----------|-------|
| W_g = 350/π | **111.408460** |
| κ (documented) | **0.8500** |
| e/π | **0.865256** (Δ from κ: **1.76%**) |
| Θ_link | **≈ π** (3.128 rad) |
| θ_crit = π(1+κ) | **5.812 rad** |

## Residual scaling

| Quantity | Value |
|----------|-------|
| π²(e/π − κ) at κ=0.85 | **≈ 0.15057** (9.5% from R) |
| κ* nulling bound exactly | **e/π − R/π² ≈ 0.8513** (0.15% from κ_doc) |

## Simulation probes

| Probe | Key result |
|-------|------------|
| PDE uniform IC | ⟨θ⟩≈0.084, σ≈0 — full-grid correlation length |
| PDE structured IC | two_gyro σ≈**0.10** @ nt=400; hopfion σ≈**0.009**; uniform σ≈**0.0002** |
| κ* (bound null) | **0.8513** (0.16% from κ_doc) |
| Conduit angular | ~8.4% / 5.7% / 4.4% within 5° of 30°/60°/90° |
| Meta-optimizer | κ=0.85, φ_b≈0.754, W_g≈111.89 — not e/π or φ⁻¹ |

## Framing

**Compatible emergent signature** — not an exact identity, not forced by invariants, not contradicted by simulation.