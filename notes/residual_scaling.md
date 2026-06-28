# Residual Scaling — π²(e/π − κ) and κ*

## Definitions

```
R  = φ² + e² − π² ≈ +0.137486
B(κ) = π²(e/π − κ) = πe − κπ²
```

## Exact null

Setting B(κ*) = R:

```
e/π − κ* = R/π²   ⟹   κ* = e/π − R/π² ≈ 0.8513
```

| κ | B(κ) | Δ from R |
|---|------|----------|
| 0.8500 (documented) | 0.15057 | 9.5% |
| 0.8513 (κ*) | 0.13749 | ~0% |

κ* is **0.15%** from documented κ = 0.85.

## Interpretation (cautious)

In the effective low-energy Skyrme + global holonomy picture:

- **π²** enters from topological / fiber geometry (circular S¹ sector).
- **(e/π − κ)** is the holonomy gap between exponential drive scale and locked pointer damping.
- The near-equality B(κ_doc) ≈ R suggests the model's κ may sit near the value that **minimizes** a Pythagorean mismatch between φ, e, and π sectors — but this is a **numerical consistency**, not a variational theorem.

## What would strengthen this

1. Derive B(κ) from the reduced action after integrating out fast quaternion modes.
2. Show κ = 0.85 is a stationary point of |B(κ) − R| under W_g-constrained dynamics.
3. Falsify: if meta-optimizer drifts κ away from 0.85 under extended trials, the scaling story weakens.

## Reproduce

```bash
python scripts/residual_kappa_sweep.py
```

See `outputs/residual_kappa_sweep.png`.