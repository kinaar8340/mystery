# Water-Phase Analog (Interpretive)

**Not H₂O thermodynamics.** A falsifiable control-plane map of solid / liquid /
vapor-like regimes onto order parameters already implemented in the Hopf stack
(mystery · oam_flux · kingdom · toe · flux_hopf_lib).

---

## Fit assessment

| Water concept | Stack analog | Strength | Notes |
|---------------|--------------|----------|-------|
| Ice (locked, low mobility) | High island-like stability + low burst rate + structured IC survival | **Strong** | Magic Island + hopfion/helix seeds |
| Liquid / brackish | Intermediate cohesion, finite σ, recovery after kicks | **Very strong** | Named regime the code already explores most |
| Vapor / gas | Weak gauge, high pointer chaos, survival collapse | **Strong** | Lattice chaotic mode at low gauge |
| Latent heat / first-order | Burst at θ_crit or W_g integrate-and-fire | **Good** | Clock / burst sink B(θ) |
| Critical point | Holonomy-gap sign change near e/π | **Reasonable** | Drive vs damping dominance flip |
| Triple point | Coexistence of attractors | **Plausible** | Not multi-attractor scanned yet |
| Ice density anomaly | Expanded vs dense lock packings | **Weak** | No quantitative density proxy |

Brackish is the best hook — already a deliberate transitional regime in the repo
(`notes/brackish_dynamics.md`, Demo J).

---

## Script

```bash
cd mystery

# Default 9×9 κ × Δω phase map (helical IC)
python scripts/water_phase_analog_sweep.py

# Smoke test
python scripts/water_phase_analog_sweep.py --quick

# Alternate PDE seeds
python scripts/water_phase_analog_sweep.py --ic hopfion
python scripts/water_phase_analog_sweep.py --ic tetrahedral

# Stress test: tetrahedral / hopfion / helical / uniform at fixed (κ, Δω)
# (includes persistence_time + structure decay curves)
python scripts/water_phase_analog_sweep.py --stress-ic
python scripts/water_phase_analog_sweep.py --stress-ic --fix-kappa 0.89 --fix-domega 0.02

# Multi-region: which seed wins across solid / liquid / vapor bands
python scripts/water_phase_analog_sweep.py --stress-ic-map

# Third axis: recovery τ × memory + exp vs stretched-exp curve shape
python scripts/water_phase_analog_sweep.py --recovery-slice

# Retune thresholds without editing logic
python scripts/water_phase_analog_sweep.py --thr-solid-identity-min 0.65 --thr-vapor-drive-min 0.12
```

### Outputs

| Mode | PNG | JSON prefix |
|------|-----|-------------|
| κ × Δω map | `outputs/water_phase_analog_heatmap.png` | `water_phase_analog_sweep_` |
| IC stress | `water_phase_ic_stress.png` (+ `_decay.png`) | `water_phase_ic_stress_` |
| IC map | `water_phase_ic_stress_map.png` | `water_phase_ic_stress_map_` |
| Recovery slice | `water_phase_recovery_slice.png` | `water_phase_recovery_slice_` |

---

## Axes

| Axis | Symbol | Role in stack | Water-like reading |
|------|--------|---------------|--------------------|
| X | κ | Gauge damping | Cohesion / pressure-like |
| Y | Δω (log) | Two-gyro drive | Temperature / heat-like |
| Z (optional) | τ_rec, memory | oam_flux recovery | Viscosity / glassiness / supercooling |

Fixed PDE horizon (`nt·dt`) is intentional: λt=2 normalization would hide
drive-dependent “temperature” differences.

---

## Dual probes

1. **PDE** — mean survival \(S\), fluctuation survival \(F\), structure retention,
   holonomy gap \(B(\kappa)=\pi^2(e/\pi-\kappa)\), burst risk.
2. **Multi-site two-gyro lattice** — absolute identity \(|\langle q,q_0\rangle|\),
   burst rate, pointer variance, island-like
   `stability_score = identity / (1 + 10·burst_rate)`.

---

## Labels — retune without editing logic

All knobs live in `LabelThresholds` / `LABEL_THRESHOLDS` at the **top** of
`scripts/water_phase_analog_sweep.py`. CLI: `--thr-<field-with-dashes>`.

| Phase | Default criteria |
|-------|------------------|
| **solid** | identity ≥ 0.62, burst_rate ≤ 0.015, drive/damp ≤ 0.04, calm pointer |
| **liquid** | brackish mid-plane (default fertile zone) |
| **vapor** | ≥2 of: high bursts, low identity, high drive/damp |
| **supercritical** | drive/damp ≥ 0.08 and \|κ − e/π\| ≤ 0.12 |

Priority: supercritical → solid → vapor → liquid.

### Example 9×9 run (defaults, helical IC)

| Phase | Count |
|-------|------:|
| solid | 15 |
| liquid | 49 |
| vapor | 15 |
| supercritical | 2 |

Pattern: **solid** at high-κ / low-Δω; **vapor** at high drive or burst chaos;
**liquid** fills the broad mid-plane; thin **supercritical** pocket near e/π.

---

## Stress tests

### 1. IC topology (`--stress-ic`)

Compares **tetrahedral / hopfion / helical / uniform** at fixed (κ, Δω).

Metrics:

| Column | Meaning |
|--------|---------|
| `struct_ret` | final / initial 3D FFT non-DC power |
| `F` | fluctuation survival |
| `t_persist` | first time structure_retention drops below `--persist-threshold` (default 0.02) |
| decay curves | `*_decay.png` — full struct_ret(t) per seed |

Question: does local topology boost structure retention *and* lifetime relative
to random noise?

Example @ κ=0.85, Δω=0.01 (nt=600, persist thr=0.02):

| IC | struct_ret | F | t_persist |
|----|------------|---|-----------|
| helical | **3.3e-2** | **0.182** | **0.60** (full horizon) |
| hopfion | 5.0e-3 | 0.071 | 0.34 |
| tetrahedral | 2.3e-3 | 0.048 | 0.28 |
| uniform | 1.0e-4 | 0.010 | 0.08 |

Persistence ranks the same as structure here: helical ≫ hopfion ≳ tetrahedral ≫
uniform. Extended topological order outlasts local tetrahedral geometry under
the 3D FFT metric (which rewards longer-range correlations).

### 2. Multi-region IC map (`--stress-ic-map`)

Runs the stress suite on a small set of (κ, Δω) bands (solid edge, liquid mid,
vapor hot, near e/π, …). Reports **which seed wins structure** and **which wins
persistence** per band, plus aggregate win counts.

**Default 8-band quick map result:** helical won **all 8** bands on both
structure_retention and persistence_time. Tetrahedral never overtook helical
near the solid boundary under current seeds/metric — a clean negative result
worth keeping (falsifies a naive “tetrahedral = ice winner” claim).

### 3. Recovery / glassiness (`--recovery-slice`)

Sweeps `recovery_tau` × `memory` at fixed (κ, Δω) after mid-run pump-off.

Also fits the post-pump load curve:

- **exponential** \(L(t) = L_∞ + A e^{-t/τ}\)
- **stretched-exp (Kohlrausch)** \(L(t) = L_∞ + A e^{-(t/τ)^β}\)

Preference stored per point (`recovery_preferred`, `beta`, `delta_r2`). Fit
signal is **structure_retention during recovery** (not load |θ−θ₀|, which is
near-pure exp by construction of the recovery step). Plot shows final structure
vs τ and fraction stretched-exp vs τ.

Example: ~52% of points prefer Kohlrausch-like (β ≠ 1, ΔR² ≥ 0.02), mostly at
**larger τ** — consistent with glassier return under high viscosity.

Question: can large τ + high memory produce glass-like stickiness, and does
return look simple-exp or stretched?

### 4. Packing density proxy (`packing_density_proxy.py`)

Negative melting-slope / ice-density-anomaly analog:

```bash
python scripts/packing_density_proxy.py
python scripts/packing_density_proxy.py --quick
# Longer multi-κ ladder (solid → liquid → vapor neighborhoods)
python scripts/packing_density_proxy.py --multi-kappa
python scripts/packing_density_proxy.py --multi-kappa --quick
```

Proxies on the relaxed twist field:

| Proxy | Meaning |
|-------|---------|
| `packing_open` | \(1/(1+\mathrm{mean}|\nabla\theta|)\) — high = open / expanded |
| `island_radius` | \(\mathrm{std}(\theta)/\mathrm{mean}|\nabla\theta|\) |
| `packing_dense_island` | \(1/(\mathrm{island\_radius}+\varepsilon)\) |
| `locked_fraction` | lattice sites with \(\lvert\langle q,q_0\rangle\rvert \ge 0.55\) |

Sweep IC amplitude; plot `stability_score` vs `packing_open`.
**Positive** per-IC slope (open more stable) = ice-density anomaly analog.
`--multi-kappa` maps that slope across a κ ladder.

**Robust anomaly score** (multi-κ):

\[
\text{anomaly\_score} = f_{\mathrm{open}} \times \langle \mathrm{slope}_+\rangle
\]

where \(f_{\mathrm{open}}\) is the fraction of ICs with slope > 0 and
\(\langle\mathrm{slope}_+\rangle\) is the mean of those positive slopes.
Helical open-favored band is highlighted on the κ ladder plot.

### 5. Minimal H₂O toy (`h2o_toy_minimal.py`)

Three flywheels (O + 2H) with soft and/or hard H–O–H angle:

```bash
python scripts/h2o_toy_minimal.py                       # default: hybrid
python scripts/h2o_toy_minimal.py --constraint both     # soft sweep + hard
python scripts/h2o_toy_minimal.py --constraint soft
python scripts/h2o_toy_minimal.py --bond-stiffness 0.4  # optional O–H length
python scripts/h2o_toy_minimal.py --quick
```

| Mode | Mechanism | Best for |
|------|-----------|----------|
| **Option A soft** | \(V=(k/2)(\angle-\angle^*)^2\) | tetrahedral / right, tunable k |
| **Option B hard** | exact geometric projection each step | **linear 180°** (soft is singular) |
| **hybrid** (default) | soft for tet/right; hard for linear | production “best of both” |
| **bond** | \(V=(k_b/2)(|r_{\mathrm{OH}}|-L^*)^2\) | optional molecular length feel |

Geometries: **free / tetrahedral (~109.47°) / right (90°) / linear (180°)**.

### 6. Multi-attractor triple-point scan (`triple_point_scan.py`)

Coexistence of solid / liquid / vapor labels at one (κ, Δω) via IC×seed ensemble:

```bash
python scripts/triple_point_scan.py
python scripts/triple_point_scan.py --quick
```

| Flag | Meaning |
|------|---------|
| `n_phases ≥ 2` | bistable / multi-attractor |
| `n_phases ≥ 3` | **triple-like** coexistence |
| `phase_entropy` | Shannon H of phase distribution |

Prints `BEST_MULTI_ATTRACTOR: …` and writes `triple_point_scan.png`.

### 7. Suite status (interpretive layer complete)

| Tool | Role |
|------|------|
| `water_phase_analog_sweep.py` | κ×Δω phase map + IC stress + recovery |
| `packing_density_proxy.py` | open-packing anomaly score + multi-κ |
| `h2o_toy_minimal.py` | molecular geometry (hybrid default) |
| `triple_point_scan.py` | multi-attractor coexistence |

Future (optional, heavier): lattice embedding of the H₂O trimer (Option C).

---

## Relation to the stack

| Stack object | Phase role |
|--------------|------------|
| Magic Island / noble locks | solid |
| Brackish dynamics / Demo J | liquid |
| Chaotic lattice (low gauge) | vapor |
| Burst at θ_crit, W_g clock | latent heat |
| B(κ) sign flip near e/π | critical-like |
| oam_flux recovery_tau | viscosity / glass |

Markers κ_doc = 0.85, κ_sim ≈ 0.89, e/π ≈ 0.865 are drawn on the heatmap as
**reference lines**, not ice/steam fixed points.

---

## Falsification

The analog is weak if, under reasonable thresholds:

- labels collapse to a single phase across the (κ, Δω) plane, or
- structured ICs never outperform uniform on structure retention, or
- recovery never increases structure retention with τ.

A useful map shows solid at high-κ/low-Δω, vapor at high drive or high burst,
and liquid (brackish) in between.
