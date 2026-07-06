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
| 0 | Triangle angle derivation | **Documented** — [angle_derivation.md](angle_derivation.md); 3-6-9 mapping still interpretive |
| 1 | Closed form for φ, e, π | Best near-miss: π²(e/π−κ) ≈ 0.151 vs R ≈ 0.137 (9.5% off) |
| 4 | κ vs e/π | κ = 0.85 is attractor; e/π is independent ~1.8% near-miss |
| 7 | φ_b | Meta best ≈ 0.754 (3/4 anyonic); not φ⁻¹ |
| 8 | Conduit 369 flags | ~8% near 30°; modest, not locked |

## Prioritized next moves

### 1. Extend structured PDE (in progress)

`pde_structured_ic_probe.py` seeds hopfion blobs and two-gyro helices — retains σ>0 and finite-k FFT vs uniform IC. Next: longer nt, finer grid, φ/e/π wavelength ratio tracking.

### 2. Formal residual bound (in progress)

`residual_kappa_sweep.py` shows **κ* = e/π − R/π² ≈ 0.8513** (0.15% from κ_doc). See `notes/residual_scaling.md`. Need variational derivation from Skyrme + holonomy.

### 3. Rodin cycle ↔ S³ fiber phase (scaffolded)

`rodin_hopf_fiber_map.py` maps 1-2-4-8-7-5 to tens_degrees / ninth_turn / hopf_weighted increments. Open: falsify against lattice burst-reset ΔΘ.

### 4. Longer conduit + island-bake runs

`vortex_math_369=True` + `toroidal_modulo9=True` with island configurations from `toe/scripts/epoch_bake_sweep.py`.

### 5. Stage 6 meta-optimization (implemented)

`meta_optimize_phi_probe.py` now supports analog objective:

- `--use-survival-penalty` — \|mean_survival − R\| at λt=2
- `--golden-angle-steps` + `--golden-reward-weight` (default 0.3)
- `--use-hybrid-objective` — hybrid Δ% instead of raw survival error
- `--compare-baseline` — baseline vs survival vs dual-analog in one JSON

**Open:** Does dual-analog optimization drift κ away from 0.85 or improve mean_survival vs R without breaking W_g lock? Run with `--trials 30+` for production comparison.

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