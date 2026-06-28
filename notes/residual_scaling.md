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

| κ | B(κ) | B(κ) − R | Relative gap |
|---|------|----------|--------------|
| 0.8500 (documented) | 0.15057 | +0.01308 | 9.5% of R |
| 0.8513 (κ*) | 0.13749 | ≈ 0 | ~0% |

κ* is **0.16%** from documented κ = 0.85.

![κ sweep: B(κ) vs R and holonomy-gap error](../docs/figures/residual_kappa_sweep.png)

---

## Interpretation

**κ* is not claimed to be the physical value.** It is the value of κ that would make the simple one-parameter scaling B(κ) = π²(e/π − κ) exactly equal to the Pythagorean residual R.

The noteworthy observation is that this exact-null κ* sits only **0.16%** from the model's locked invariant κ = 0.85 — while at κ_doc itself, B(κ) remains **~9.5%** above R. So:

- The scaling thread is **strengthened** (the holonomy gap e/π − κ appears to govern the residual scale).
- An **identity is not claimed** (documented κ does not null R; meta-optimizer does not pull toward e/π).
- The proximity of κ* to κ_doc suggests the TOE's choice of global pointer damping may sit near the value that would make the effective low-energy mismatch vanish — a **compatible emergent signature**, not a derived theorem.

In the Skyrme + global holonomy picture:

- **π²** enters from topological / circular S¹ fiber geometry.
- **(e/π − κ)** is the holonomy gap between exponential drive scale and locked pointer damping.
- R may scale with that gap in the reduced theory — worth formalizing, not yet derived.

---

## What would strengthen this

1. Derive B(κ) from the reduced action after integrating out fast quaternion modes.
2. Show κ = 0.85 is a stationary point of |B(κ) − R| under W_g-constrained dynamics.
3. Falsify: if extended meta-optimizer trials drift κ away from 0.85, the scaling story weakens.

## Reproduce

```bash
python scripts/residual_kappa_sweep.py
```

Output: `outputs/residual_kappa_sweep.png` (copied to `docs/figures/` for the repo).