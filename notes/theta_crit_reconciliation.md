# θ_crit Reconciliation (June 2026)

## Problem

Two numerically different values were conflated:

| Source | Value | Notes |
|--------|-------|-------|
| `pde_relaxation.py`, lattice demos | **5.8 rad** | Burst sink threshold |
| Hopf formula in old PDF | **2π·W_g/(2W_g+1)** | Evaluates to **≈ 3.13 rad ≈ π**, not 5.8 |

The April 2026 `GW_Burst_Threshold.pdf` incorrectly wrote `≈ 5.8` next to the linking formula.

## Resolution

Two distinct thresholds:

### 1. Θ_link — Hopf linking saturation

```
Θ_link = 2π · W_g / (2W_g + 1)   with W_g = 350/π
       ≈ 3.128 rad ≈ π
```

Geometric bound: antipodal point on the Hopf S¹ fiber. Protects quantized linking.

### 2. θ_crit — effective burst threshold (simulations)

```
θ_crit = π(1 + κ)   with κ ≈ 0.85
       ≈ 5.812 rad ≈ 5.8
```

Holonomy-lifted operational threshold used in PDE and lattice code. Bare fiber limit π plus margin κπ from global pointer α = −κΘ̄.

## Updated document

`~/Projects/toe/papers/GW_Burst_Threshold.pdf` (June 2026 revision) — source: `GW_Burst_Threshold.tex`.

## Meta-optimizer check (12 trials)

Best trial clustered on **documented** constants, not φ/e/π transcendentals:

| Parameter | Best | Nearest attractor |
|-----------|------|-------------------|
| κ | 0.8500 | κ_doc (not e/π = 0.865) |
| wg_base | 351.5 | 350 (W_g = 111.89) |
| φ_b | 0.754 | 3/4 anyonic (not φ⁻¹) |

κ locks to 0.85 exactly; e/π remains a ~1.8% near-miss, not the optimizer attractor.