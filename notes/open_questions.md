# Open Questions & Next Moves

## Resolved

| # | Item | Outcome |
|---|------|---------|
| 2 | Kepler triangle contrast | Kepler exact; φ-e-π approximate — three transcendental families |
| 3 | High-precision residual | R stable; drift &lt; 1e−10 |
| 5 | θ_crit dual definitions | Θ_link ≈ π; θ_crit = π(1+κ) ≈ 5.8 — see `theta_crit_reconciliation.md` |
| 6 | PDE uniform relaxation | No φ/e/π FFT signature — expected for this IC class |
| 9 | Why κ_sim ≈ 0.89 vs κ_doc = 0.85? | **Closed** — static κ_doc (θ_crit, B(κ), training seed) vs dynamic κ_sim (λ≈κ survival optimum @ λt=2 ≈0.891; holonomy-gap regime crossing κ > e/π; 369 κ_proxy→κ_sim). See [`docs/RESULTS.md`](../docs/RESULTS.md) § Physical interpretation · [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md) |

## Active (partially answered)

| # | Item | Status |
|---|------|--------|
| 0 | Triangle angle derivation | **Documented** — [angle_derivation.md](angle_derivation.md); 3-6-9 mapping still interpretive |
| 1 | Closed form for φ, e, π | Best near-miss: π²(e/π−κ) ≈ 0.151 vs R ≈ 0.137 (9.5% off) |
| 4 | κ vs e/π | **Dual-role κ:** κ_doc = 0.85 (theory anchor); κ_sim ≈ 0.89 (island+survival optimum); κ* ≈ 0.8513 (exact null). e/π is independent ~1.8% near-miss |
| 7 | φ_b | Meta best ≈ 0.754 (3/4 anyonic); not φ⁻¹ |
| 8 | Conduit 369 flags | ~8% near 30°; modest, not locked |

## Prioritized next moves

### 1. Extend structured PDE (in progress)

`pde_structured_ic_probe.py` seeds hopfion blobs and two-gyro helices — retains σ>0 and finite-k FFT vs uniform IC. Next: longer nt, finer grid, φ/e/π wavelength ratio tracking.

### 2. Formal residual bound (in progress)

`residual_kappa_sweep.py` shows **κ* = e/π − R/π² ≈ 0.8513** (0.15% from κ_doc). Variational sketch in [`kappa_star_variational.md`](kappa_star_variational.md). Still need full π² prefactor derivation from reduced Skyrme action.

### 3. Rodin cycle ↔ S³ fiber phase (scaffolded)

`rodin_hopf_fiber_map.py` maps 1-2-4-8-7-5 to tens_degrees / ninth_turn / hopf_weighted increments. Open: falsify against lattice burst-reset ΔΘ.

### 4. Topology κ bake grid — **mostly closed** (July 2026)

`epoch_bake_sweep.py --topology-grid` + `magic_island_sweep.py --topology-grid --island-z 129`. **vortex_math_369** shifts κ_proxy → κ_sim (0.885). **braid_feedback_gain = 0.002** (tuned from 0.02). Magic-island bake anchors κ_final ≈ 0.849 (|drift| &lt; 0.002); bare bake still over-drifts. See `docs/RESULTS.md` Stage 8/8b, `notes/kappa_star_variational.md`.

### 5. Stage 6 meta-optimization — **closed** (July 2026)

Dual-analog objective converges to **κ_sim ≈ 0.89**, W_g ≈ 111.41, mean_survival = 0.137651, Δ% vs R = 0.121%, dual-analog loss = **56.98**. W_g lock holds; survival alignment improved vs pilot (0.355% → 0.121%). Squared κ prior (w_κ ≤ 500) does not shift κ.

**κ_doc vs κ_sim:** paired comparative sweep confirms κ_sim wins on best Δ% vs R (0.121% vs 0.166%) and island+Hopf loss; κ_doc marginally wins on uniform PDE hybrid. See [`docs/RESULTS.md`](../docs/RESULTS.md) Stage 7 section and [`stage6_analog_tuning.md`](stage6_analog_tuning.md).

**Production:** dual-analog, w_s=5, golden_reward_weight=0.3, hybrid survival, **no κ prior**, κ ≈ 0.89.

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