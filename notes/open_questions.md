# Open Questions & Next Moves

## Resolved

| # | Item | Outcome |
|---|------|---------|
| 2 | Kepler triangle contrast | Kepler exact; φ-e-π approximate — three transcendental families |
| 3 | High-precision residual | R stable; drift &lt; 1e−10 |
| 5 | θ_crit dual definitions | Θ_link ≈ π; θ_crit = π(1+κ) ≈ 5.8 — see `theta_crit_reconciliation.md` |
| 6 | PDE uniform relaxation | No φ/e/π FFT signature — expected for this IC class |

## Active (partially answered)

| # | Item | Status |
|---|------|--------|
| 1 | Closed form for φ, e, π | Best near-miss: π²(e/π−κ) ≈ 0.151 vs R ≈ 0.137 (9.5% off) |
| 4 | κ vs e/π | κ = 0.85 is attractor; e/π is independent ~1.8% near-miss |
| 7 | φ_b | Meta best ≈ 0.754 (3/4 anyonic); not φ⁻¹ |
| 8 | Conduit 369 flags | ~8% near 30°; modest, not locked |

## Prioritized next moves

### 1. Structured PDE initial conditions (highest priority)

Seed localized twists, Hopfions, or two-gyro counter-rotating helicities (flux flywheels). Hunt FFT peaks and correlation lengths near φ, e, π scales.

```bash
# Extend pde_relaxation_probe.py or toe/scripts/pde_relaxation.py
```

### 2. Formal residual bound

Treat R ≈ π²(e/π − κ) in the effective Skyrme + global holonomy reduction. Potentially paper-worthy if derived cleanly from the low-energy action.

### 3. Rodin cycle ↔ S³ fiber phase

Map discrete mod-9 doubling (1-2-4-8-7-5) onto continuous phase increments on Hopf S¹ fibers.

### 4. Longer conduit + island-bake runs

`vortex_math_369=True` + `toroidal_modulo9=True` with island configurations from `toe/scripts/epoch_bake_sweep.py`.

---

## Run probes

```bash
cd mystery && .venv/bin/python run_all.py
```

Upstream (optional):

```bash
cd ../toe && venv/bin/python scripts/meta_optimize_invariants.py --trials 50
cd ../toe && venv/bin/python scripts/pde_relaxation.py
```