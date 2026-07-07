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
| κ_doc (documented) | **0.8500** |
| κ_sim (simulation optimum) | **≈ 0.890** |
| e/π | **0.865256** (Δ from κ_doc: **1.76%**) |
| Θ_link | **≈ π** (3.128 rad) |
| θ_crit = π(1+κ_doc) | **5.812 rad** |

## Production vs documentation parameters

The model exhibits a mild but consistent preference: while the documented gauge value is **κ_doc = 0.85**, systematic tuning and survival alignment at λt = 2 converge near **κ_sim ≈ 0.89**. We maintain both with clearly separated roles — not a contradiction.

| Symbol | Value | Role |
|--------|-------|------|
| **κ_doc** | 0.85 | Documentation / theory: θ_crit = π(1+κ), residual scaling B(κ), Hopf lattice framing |
| **κ_sim** | ≈ 0.89 | Simulation / production: Stage 6 dual-analog optimum, best Δ% vs R, island+Hopf minimum |
| **κ\*** | ≈ 0.8513 | Exact mathematical null: e/π − R/π² (0.16% from κ_doc) |

**Production meta-opt:** dual-analog, w_s = 5, golden_reward_weight = 0.3, hybrid survival, **no κ prior**, κ = **κ_sim ≈ 0.89**, W_g ≈ 111.41, loss **56.98**.

**Documentation:** retain κ_doc = 0.85 in formulas, nulling discussion, and browser κ slider default.

Paired sweep (Stage 7): κ_sim wins best Δ% vs R (0.121% vs 0.166%) and island+Hopf loss; κ_doc marginally wins uniform PDE hybrid. See Stage 7 section below.

## Physical interpretation — κ_sim vs κ_doc (Q#9 closed)

The ~4% gap |κ_sim − κ_doc| ≈ 0.04 is **not a contradiction**. κ enters the gauged Hopf lattice in two distinct physical senses:

| Sense | Symbol | Value | Question it answers |
|-------|--------|-------|---------------------|
| **Static** | κ_doc | 0.85 | What κ defines θ_crit, B(κ) framing, and training seeds? |
| **Algebraic** | κ\* | ≈ 0.8513 | What κ nulls B(κ) = π²(e/π−κ) = R exactly? |
| **Dynamic** | κ_sim | ≈ 0.89 | What κ minimizes survival misalignment at λt = 2 under tuned dynamics? |

### κ as a dissipation rate

In the mean-field twist-PDE reduction, gauge torque **−κθ̄** identifies effective rate **λ ≈ κ**. At normalized time λt = 2, step count is n = (λt/κ)/dt — higher κ means stronger per-step damping and a different mean survival fraction.

κ-survival sweep (uniform IC, λt = 2):

| κ | mean_survival | Δ% vs R |
|---|---------------|---------|
| 0.8500 (κ_doc) | 0.137606 | 0.088% |
| 0.8513 (κ\*) | ≈ 0.1375 | ≈ 0.05% |
| 0.8900 (κ_sim) | 0.137652 | 0.121% |
| **0.8909** (sweep best) | **0.137506** | **0.015%** |

**Primary pull toward κ_sim:** survival alignment at λt = 2 peaks near κ ≈ 0.891, not κ_doc. Stage 7 conduit Δ% improves **0.166% → 0.121%**; 70-run robust grid holds conduit metrics identical across twist 8–17.5 and step modes.

**Secondary:** island+Hopf+braiding base loss is nearly κ-flat (~0.05 spread over κ ∈ [0.8, 0.9]); κ prior w_κ ≤ 500 cannot pull κ back to 0.85.

### Holonomy-gap regime crossing

| κ | e/π − κ | B(κ) = π²(e/π−κ) | Regime |
|---|---------|-------------------|--------|
| κ_doc 0.85 | +0.0153 | +0.1506 (9.5% above R) | Positive gap — drive > damping |
| κ\* 0.8513 | +0.0139 | ≈ R (exact null) | Algebraic null |
| e/π 0.8653 | 0 | 0 | Crossover |
| **κ_sim 0.89** | **−0.0247** | negative | **Damping-dominated** (κ > e/π) |

κ_sim does **not** null B(κ) = R — that is κ\*. It optimizes **dynamic** survival. θ_crit rises from **5.81 rad** @ κ_doc to **~5.94 rad** @ κ_sim (~2% more burst headroom).

### Topology readout (Stage 8)

**vortex_math_369** shifts holonomy **κ_proxy** from ~0.854 → **~0.885** (κ_sim neighborhood) without forcing adaptive **κ_final** there under gentle braid gain (magic-island κ_final ≈ 0.849 @ gain 0.002). Interpretation: trained pointer anchors near κ_doc; active vortex sector **measures** emergent holonomy consistent with κ_sim.

### Synthesis

κ_doc = 0.85 is the **static** global pointer constant (θ_crit, B(κ) framing, training seed, 0.16% from κ\*). κ_sim ≈ 0.89 is the **dynamic** dissipative optimum where λ ≈ κ survival at λt = 2 best tracks R. The shift is not toward e/π (0.865) — it crosses into a damping-dominated holonomy regime. Production uses κ_sim; documentation retains κ_doc.

Extended note: [`notes/kappa_sim_interpretation.md`](../notes/kappa_sim_interpretation.md).

## Formal Skyrme + holonomy derivation (B(κ) — Q#2 closed)

From `Lagrangian_Derivation.pdf` mean-field free energy \(\mathcal{F}_0 = \frac{\kappa}{2}\bar\theta^2 - \Delta\omega\bar\theta\) and Hopf fiber saturation \(\Theta_\star = \pi\):

\[
\Phi_{\mathrm{drive}} = \pi \cdot (e/\pi) = e, \qquad
\Phi_{\mathrm{damp}}(\kappa) = \kappa\pi^2, \qquad
B(\kappa) = \pi\Phi_{\mathrm{drive}} - \Phi_{\mathrm{damp}} = \pi^2(e/\pi - \kappa).
\]

Setting \(B(\kappa^\ast) = R\) gives **κ\* = e/π − R/π² ≈ 0.8513** (0.16% from κ_doc). Full write-up: [`notes/skyrme_holonomy_derivation.md`](../notes/skyrme_holonomy_derivation.md). Verify:

```bash
python scripts/skyrme_bound_derivation.py
```

Open beyond mean-field: nonlinear cot(θ/2) corrections; PDE eigenstructure for survival minimum at κ ≈ 0.891.

## Residual scaling

| Quantity | Value |
|----------|-------|
| π²(e/π − κ) at κ=0.85 | **≈ 0.15057** (9.5% from R) |
| κ* nulling B(κ)=R exactly | **e/π − R/π² ≈ 0.8513** (0.16% from κ_doc) |
| B(κ_doc) − R | **+0.0131** (9.5% of R) — identity not claimed |

## Simulation probes

| Probe | Key result |
|-------|------------|
| PDE uniform IC | ⟨θ⟩≈0.084, σ≈0 — full-grid correlation length |
| PDE structured IC | two_gyro σ≈**0.10** @ nt=400; hopfion σ≈**0.009**; uniform σ≈**0.0002** |
| κ* (bound null) | **0.8513** (0.16% from κ_doc) |
| Conduit angular | ~8.4% / 5.7% / 4.4% within 5° of 30°/60°/90° |
| Meta-optimizer | κ=0.85, φ_b≈0.754, W_g≈111.89 — not e/π or φ⁻¹ |

## Analog objective (Stage 6)

`meta_optimize_phi_probe.py` supports an optional survival penalty at λt = 2:

```
loss = base_loss + w_s × survival_term + w_κ × (κ − κ_target)² − golden_reward
survival_term = |mean_survival − R|   (or hybrid_delta_pct/100 with --use-hybrid-objective)
golden_reward   = weight × (0.5×golden_closeness + 0.5×S¹ packing)   when --golden-angle-steps
```

| Flag | Purpose |
|------|---------|
| `--use-survival-penalty` | Penalize deviation of PDE mean_survival from R at λt=2 |
| `--golden-angle-steps` | Enable golden helix + golden reward term (dual_analog only in compare mode) |
| `--golden-reward-weight` | Default 0.3 |
| `--use-hybrid-objective` | Use hybrid Δ% instead of raw \|mean_survival − R\| |
| `--use-kappa-prior` | Penalize `(κ − κ_target)²` toward κ_doc (default target 0.85) |
| `--kappa-prior-weight` | Weight w_κ on squared κ deviation (default 50) |
| `--kappa-prior-target` | Prior center (default 0.85) |
| `--compare-baseline` | Run baseline vs survival vs dual-analog in one report |

**Pilot run (8 trials each, July 2026):**

| Mode | Best loss | κ | mean_survival | Δ% vs R | hybrid |
|------|-----------|---|---------------|---------|--------|
| baseline | 63.92 | 0.77 | — | — | — |
| survival_penalty | 63.92 | 0.77 | 0.137974 | 0.355% | 0.9987 |
| dual_analog | **63.64** | 0.77 | 0.137974 | 0.355% | 0.9987 |

Dual-analog lowers loss via golden_reward (0.275) without changing best κ in this small run. Increase `--trials` and `--survival-penalty-weight` to test κ drift vs documented 0.85.

### Stage 6 — 30-trial analog objective tuning (w_s=5.0)

Command: `meta_optimize_phi_probe.py --compare-baseline --trials 30 --use-survival-penalty --golden-angle-steps --golden-reward-weight 0.3 --use-hybrid-objective --survival-penalty-weight 5`

| Mode | Best loss | κ | mean_survival | Δ% vs R | hybrid |
|------|-----------|---|---------------|---------|--------|
| baseline | 57.22 | 0.89 | — | — | — |
| survival_penalty | 57.26 | 0.89 | 0.137651 | 0.121% | 0.9990 |
| dual_analog | **56.98** | 0.89 | 0.137651 | 0.121% | 0.9990 |

At w_s = 5.0, κ drifts from pilot 0.77 → 0.89 (|κ−0.85| halved). Dual-analog lowers loss via golden_reward (0.275) while improving survival alignment (Δ% vs R: 0.355% → 0.121%). JSON: `outputs/meta_optimize_phi_probe_20260706_231311.json`.

### Stage 6 — w_s sensitivity sweep (25 trials per mode)

Command: `w_s_sweep.py --weights 8 10 12 --trials 25` (includes w_s=5 reference from 30-trial run).

| w_s | baseline | survival_penalty | dual_analog | κ | mean_survival | Δ% vs R | hybrid |
|-----|----------|------------------|-------------|---|---------------|---------|--------|
| 5.0 | 57.22 | 57.26 | **56.98** | 0.89 | 0.137651 | 0.121% | 0.9990 |
| 8.0 | 57.22 | 57.28 | **57.01** | 0.89 | 0.137651 | 0.121% | 0.9990 |
| 10.0 | 57.22 | 57.30 | **57.02** | 0.89 | 0.137651 | 0.121% | 0.9990 |
| 12.0 | 57.22 | 57.31 | **57.04** | 0.89 | 0.137651 | 0.121% | 0.9990 |

κ and survival metrics are **stable across w_s ∈ [5, 12]** — all runs lock to the κ-sweep optimum (~0.89). **w_s = 5** gives the best dual-analog loss; higher weights only increase the survival penalty term (e.g. w_s×term = 0.037 → 0.090 at w_s=12) without shifting κ toward 0.85. JSON: `outputs/w_s_sweep_20260706_233453.json`.

### Stage 6 — 50-trial confirmation (w_s=5.0)

Command: `meta_optimize_phi_probe.py --compare-baseline --trials 50 … --survival-penalty-weight 5`

| Mode | Best loss | κ | W_g | mean_survival | Δ% vs R | hybrid |
|------|-----------|---|-----|---------------|---------|--------|
| baseline | 57.22 | 0.89 | 111.41 | — | — | — |
| survival_penalty | 57.26 | 0.89 | 111.41 | 0.137651 | 0.121% | 0.9990 |
| dual_analog | **56.98** | 0.89 | 111.41 | 0.137651 | 0.121% | 0.9990 |

**Identical to the 30-trial run** — TPE converged by trial ~22; 50 trials confirm stability. JSON: `outputs/meta_optimize_phi_probe_20260706_233925.json`.

### Stage 6 — robustness sweep at meta-opt best point (κ=0.89, W_g=111.41)

**Standard grid** (18 runs): `analog_comparative_sweep.py --kappa 0.89 --wg-base 350.0`  
3 IC × 2 λt + 3 twist × 2 λt × 2 step modes.

| Metric | Value |
|--------|-------|
| Best Δ% vs R | **0.121%** (conduit, λt=2, all twist rates) |
| Best hybrid score | **0.9990** (conduit + PDE @ λt=2) |
| mean_survival @ λt=2 | **0.137651** (matches meta-opt) |
| Top synergy (golden+λt=2) | hybrid **0.9990**, packing ≈ 0.78 |

JSON: `outputs/analog_comparative_sweep_20260706_233723.json`.

**Expanded robust grid** (70 runs): `--robust --kappa 0.89 --wg-base 350.0`  
6 IC types, 5 uniform seeds, λt ∈ {None, 1.5, 2.0, 2.5}, twist rates 8–17.5, linear + golden conduit steps.

| Subsystem @ λt=2 | n | Δ% vs R (min–max) | hybrid (min–max) | mean_survival |
|------------------|---|-------------------|------------------|---------------|
| **All** | 20 | **0.121%** – 5.20% (mean 0.81%) | 0.9921 – **0.9991** | 0.137 – 0.145 |
| PDE | 10 | 0.28% – 5.20% | 0.9921 – 0.9991 | 0.137 – 0.145 |
| **Conduit** | 10 | **0.121%** (identical) | **0.9990** (identical) | **0.137651** |

**Finding:** Conduit survival alignment is **perfectly stable** across twist rates 8–17.5 and step modes at κ_sim = 0.89. PDE structured ICs (hopfion @ λt=2) show higher Δ% (~5%) as expected; uniform IC across 5 seeds is stable (Δ% ≈ 0.28%). Best @ λt=2: conduit linear twist=8, Δ% = **0.121%**.

JSON: `outputs/analog_comparative_sweep_20260707_012224.json`.

### Stage 6 — κ prior experiment (w_κ ∈ {50, 500}, w_s=5, 30 trials)

Command: `meta_optimize_phi_probe.py --compare-baseline --trials 30 --use-survival-penalty --golden-angle-steps --golden-reward-weight 0.3 --use-hybrid-objective --survival-penalty-weight 5 --use-kappa-prior --kappa-prior-target 0.85 --kappa-prior-weight {50|500}`

| w_κ | Mode | Loss | κ | mean_survival | Δ% vs R | w_κ×term | golden_reward |
|-----|------|------|---|---------------|---------|----------|---------------|
| 50 | survival_penalty† | 57.06† | 0.89 | 0.137651 | 0.121% | 0.08 | 0.275† |
| 50 | dual_analog† | 57.06† | 0.89 | 0.137651 | 0.121% | 0.08 | 0.275 |
| **500** | survival_penalty | **58.06** | 0.89 | 0.137651 | 0.121% | 0.80 | — |
| **500** | dual_analog | **57.78** | 0.89 | 0.137651 | 0.121% | 0.80 | 0.275 |
| (ref) | dual_analog, no prior | **56.98** | 0.89 | 0.137651 | 0.121% | — | 0.275 |

†w_κ=50 run affected by a since-fixed bug (`--golden-angle-steps` leaked into survival_penalty). Use w_κ=500 row for valid comparison.

**Finding:** κ remains **0.890** at both w_κ = 50 and 500 — island+Hopf and survival both prefer κ ≈ 0.89 (baseline trial κ=0.85 → loss 58.62 vs κ=0.89 → 57.22). The prior adds cost (+0.08 @ w_κ=50, +0.80 @ w_κ=500) without shifting the optimum. At w_κ=500, dual-analog (**57.78**) no longer beats baseline (57.22).

**Production:** dual-analog **without** κ prior — loss **56.98**, κ **0.89**.

| Artifact | Path |
|----------|------|
| w_κ=50 (bugged) | `outputs/meta_optimize_phi_probe_20260707_003033.json` |
| w_κ=500 (valid) | `outputs/meta_optimize_phi_probe_20260707_003333.json` |

### Stage 7 — paired κ comparison (κ_doc vs κ_sim)

Fixed-point comparison at **W_g = 111.41** (wg_base = 350), same 18-run grid (3 IC × 2 λt + 3 twist × 2 step modes):

```bash
toe/venv/bin/python scripts/analog_comparative_sweep.py --kappa 0.85 --wg-base 350.0
toe/venv/bin/python scripts/analog_comparative_sweep.py --kappa 0.89 --wg-base 350.0
```

**PDE @ λt = 2** (primary survival probe):

| IC | mean_survival @ κ=0.85 | mean_survival @ κ=0.89 | Δ% vs R @ 0.85 | Δ% vs R @ 0.89 | hybrid @ 0.85 | hybrid @ 0.89 |
|----|------------------------|-------------------------|----------------|----------------|---------------|---------------|
| uniform | 0.137159 | 0.137096 | 0.238% | 0.284% | 0.9991 | 0.9990 |
| hopfion | 0.145053 | 0.144634 | 5.504% | 5.200% | 0.9917 | 0.9921 |
| helical | 0.138165 | 0.138057 | 0.494% | 0.416% | 0.9985 | 0.9986 |

**Conduit @ λt = 2** (all twist rates 10/12.5/15, linear + golden): identical across twist/step — best Δ% **0.166%** @ κ=0.85 vs **0.121%** @ κ=0.89; hybrid **0.9989** vs **0.9990**.

**Grid summary @ λt = 2:**

| Metric | κ = 0.85 (κ_doc) | κ = 0.89 (κ_sim) | Winner |
|--------|------------------|------------------|--------|
| Best Δ% vs R | 0.166% | **0.121%** | κ_sim |
| Best hybrid | **0.9991** | 0.9990 | κ_doc (marginal) |
| Avg mean_survival | **0.138518** | 0.138411 | κ_doc (marginal) |
| Meta-opt island+Hopf loss | ~58.6 @ κ=0.85 | **57.22 @ κ=0.89** | κ_sim |

κ survival sweep (uniform PDE, λt=2) independently shows best Δ% vs R at **κ ≈ 0.891** (0.015%); κ_doc = 0.85 gives Δ% = 0.088%.

**Decision — dual-role κ:**

| Symbol | Value | Role |
|--------|-------|------|
| **κ_doc** | 0.85 | Documented holonomy-gap parameter: θ_crit = π(1+κ), residual scaling B(κ), e/π proximity framing |
| **κ_sim** | ≈ 0.89 | Simulation optimum: island+Hopf base_loss minimum + best conduit/κ-sweep alignment with R at λt=2 |
| **κ\*** | ≈ 0.8513 | Exact null e/π − R/π² (residual bound; 0.15% from κ_doc) |

The ~4% gap between κ_doc and κ_sim is **not a contradiction** — theory anchor vs combined PDE+island optimum. **Production meta-opt uses κ_sim ≈ 0.89** (dual-analog, w_s=5, loss 56.98). **Documentation and nulling formulas retain κ_doc = 0.85.**

JSON: `outputs/analog_comparative_sweep_20260707_004010.json` (κ=0.85) · `outputs/analog_comparative_sweep_20260706_233723.json` (κ=0.89).

### Stage 8 — topology κ bake grid (2×2, 500 steps)

Command: `toe/venv/bin/python scripts/epoch_bake_sweep.py --topology-grid --bake-steps 500`  
Mystery wrapper: `scripts/topology_kappa_bake_grid.py`

κ seeded at **κ_doc = 0.85**, W_g = 111.41, adaptive κ feedback during bake.

| Config | toroidal | vortex_369 | κ_final | κ_proxy | κ_proxy nearest | vortex_sync |
|--------|----------|------------|---------|---------|-----------------|-------------|
| baseline | off | off | 0.716 | 0.854 | κ_doc (Δ 0.035) | 0.018 |
| toroidal_only | on | off | 0.716 | 0.854 | κ_doc (Δ 0.035) | 0.018 |
| vortex369_only | off | on | 0.716 | **0.885** | **κ_sim (Δ 0.005)** | 0.203 |
| full_topology | on | on | 0.716 | **0.885** | **κ_sim (Δ 0.005)** | 0.203 |

**Finding:** `vortex_math_369` shifts the holonomy-gap **κ_proxy** toward **κ_sim ≈ 0.89** (|proxy − κ_sim| = 0.005 vs 0.035 without 369). `toroidal_modulo9` alone does not change κ_proxy or κ_final. Adaptive κ_final drifts to **0.716** (floor clip) in all configs — driven by large braiding_delta (0.73 vs target 0.8145), not topology-differentiated.

**Interpretation:** 369 topology affects emergent holonomy observables (κ_proxy, vortex_sync); it does **not** uniquely determine κ_final under current bake feedback. κ_sim ≈ 0.89 from meta-opt likely arises from island+survival loss, with 369 topology as a supporting mechanism. Variational sketch: [`notes/kappa_star_variational.md`](../notes/kappa_star_variational.md).

JSON: `outputs/topology_kappa_bake_grid_20260707_005300.json`

**Braid-feedback tuning** (gain 0.02 → **0.002** default; sweep 0.002 / 0.005 / 0.01):

| braid_gain | κ_final (all configs) | κ_drift | κ_proxy (no 369) | κ_proxy (369 on) |
|------------|----------------------|---------|-------------------|-------------------|
| 0.002 | 0.837 | −0.013 | 0.854 | 0.885 |
| 0.005 | 0.816 | −0.034 | 0.854 | 0.885 |
| 0.01 | 0.783 | −0.067 | 0.854 | 0.885 |

JSON: `outputs/topology_kappa_braid_sweep_20260707_005540.json`

### Stage 8b — magic island braid-gain × topology grid (Z=129)

Command:

```bash
toe/venv/bin/python scripts/magic_island_sweep.py \
  --topology-grid --island-z 129 --quick \
  --braid-gains 0.002 0.005 0.01
```

Mystery wrapper: `scripts/magic_island_topology_grid.py`

**Island preset (magic Z=129):** layers=4, pol=9, max_facts=12 (quick), gauge=0.85, ω_R=0.0225, κ_seed=κ_doc=0.85, W_g=111.41.  
Grid: **3 braid gains × 4 topology configs** = 12 runs; adaptive κ feedback every 5 facts.

**Full 12-run table:**

| Config | toroidal | vortex_369 | braid_gain | κ_final | κ_drift | κ_proxy | |κ−κ_doc| | |κ−κ\*| | stability |
|--------|----------|------------|------------|---------|---------|---------|---------|---------|-----------|
| baseline | off | off | 0.002 | **0.849** | **−0.0015** | 0.854 | 0.0015 | 0.0028 | **8.0** |
| toroidal_only | on | off | 0.002 | **0.849** | **−0.0015** | 0.854 | 0.0015 | 0.0028 | **8.0** |
| vortex369_only | off | on | 0.002 | **0.849** | **−0.0015** | **0.885** | 0.0015 | 0.0028 | **8.0** |
| full_topology | on | on | 0.002 | **0.849** | **−0.0015** | **0.885** | 0.0015 | 0.0028 | **8.0** |
| baseline | off | off | 0.005 | 0.846 | −0.0037 | 0.854 | 0.0037 | 0.0051 | 8.0 |
| toroidal_only | on | off | 0.005 | 0.846 | −0.0037 | 0.854 | 0.0037 | 0.0051 | 8.0 |
| vortex369_only | off | on | 0.005 | 0.846 | −0.0037 | **0.885** | 0.0037 | 0.0051 | 8.0 |
| full_topology | on | on | 0.005 | 0.846 | −0.0037 | **0.885** | 0.0037 | 0.0051 | 8.0 |
| baseline | off | off | 0.01 | 0.843 | −0.0075 | 0.854 | 0.0075 | 0.0088 | 8.0 |
| toroidal_only | on | off | 0.01 | 0.843 | −0.0075 | 0.854 | 0.0075 | 0.0088 | 8.0 |
| vortex369_only | off | on | 0.01 | 0.843 | −0.0075 | **0.885** | 0.0075 | 0.0088 | 8.0 |
| full_topology | on | on | 0.01 | 0.843 | −0.0075 | **0.885** | 0.0075 | 0.0088 | 8.0 |

**Braid-gain summary (all topologies identical on κ_final):**

| braid_gain | κ_final | κ_drift | |κ−κ_doc| | |κ−κ\*| | κ_proxy (369 off) | κ_proxy (369 on) |
|------------|---------|---------|---------|---------|-------------------|-------------------|
| **0.002** | **0.849** | **−0.0015** | **0.0015** | **0.0028** | 0.854 | **0.885** |
| 0.005 | 0.846 | −0.0037 | 0.0037 | 0.0051 | 0.854 | 0.885 |
| 0.01 | 0.843 | −0.0075 | 0.0075 | 0.0088 | 0.854 | 0.885 |

**Findings:**

1. **Magic-island bake anchors κ_final near κ_doc and κ\*** — at gain=0.002, |κ_final − κ_doc| = 0.0015 and |κ_final − κ\*| = 0.0028 (vs bare epoch bake drifting to 0.716).
2. **vortex_math_369 shifts κ_proxy to κ_sim** — 0.854 without 369 → **0.885** with 369 (|proxy − κ_sim| = 0.005); toroidal alone unchanged.
3. **Topology does not differentiate κ_final** — all four configs share identical κ_final per braid gain; island stability_score = **8.0** throughout.
4. **Production braid_feedback_gain = 0.002** — tuned down from 0.02; higher gains monotonically pull κ_final below κ_doc.

**vs bare epoch bake (Stage 8):** island training prevents κ over-correction; κ_proxy behavior (369 → κ_sim) is consistent across both engines.

JSON (quick, 12 effective facts): `toe/outputs/magic_island/island_topology_grid_z129_20260707_005606.json`

**Full corpus (60 paper-derived facts, no `--quick`):**

```bash
toe/venv/bin/python scripts/magic_island_sweep.py \
  --topology-grid --island-z 129 --braid-gains 0.002 0.005 0.01
```

| braid_gain | κ_final | κ_drift | κ_proxy (369 on) | stability |
|------------|---------|---------|------------------|-----------|
| **0.002** | **0.832** | −0.018 | **0.885** | **43.0** |
| 0.005 | 0.805 | −0.045 | 0.885 | 43.0 |
| 0.01 | 0.760 | −0.090 | 0.885 | 43.0 |

vs quick (12 facts): κ_final **0.849** @ gain 0.002. Topology still flat on κ_final; **vortex_369** still shifts κ_proxy → κ_sim. Deeper training pulls κ_final below κ_doc — production **braid_feedback_gain = 0.002** remains the tuned default.

JSON (60 facts): `toe/outputs/magic_island/island_topology_grid_z129_20260707_011316.json`

## Analog sweeps (Stages 4–5)

| Probe | Key result |
|-------|------------|
| κ survival sweep | mean_survival vs R **broad** on κ ∈ [0.80, 0.90]; best Δ% ~0.015% at κ≈0.891 |
| λt=2 PDE (κ=0.85) | mean_survival = **0.137606** (Δ 0.09% vs R) |
| Comparative sweep (fast) | hybrid scores **0.9989–0.9991** |
| Golden S¹ probe | packing coverage ≈ **0.889**; phase histograms in `outputs/golden_phase_hist_*.png` |

## Framing

**Compatible emergent signature** — not an exact identity, not forced by invariants, not contradicted by simulation. κ_doc (0.85) and κ_sim (≈0.89) coexist as static documentation anchor vs dynamic simulation optimum (Q#9 closed); neither is claimed as a unique physical constant.