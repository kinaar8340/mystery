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

Command: `analog_comparative_sweep.py --kappa 0.89 --wg-base 350.0` (18 runs: 3 IC × 2 λt + 3 twist × 2 λt × 2 step modes).

| Metric | Value |
|--------|-------|
| Best Δ% vs R | **0.121%** (conduit, λt=2, all twist rates) |
| Best hybrid score | **0.9990** (conduit + PDE @ λt=2) |
| mean_survival @ λt=2 | **0.137651** (matches meta-opt) |
| Top synergy (golden+λt=2) | hybrid **0.9990**, packing ≈ 0.78 |

Alignment holds across IC types, twist rates, and step modes at the converged κ/W_g point. JSON: `outputs/analog_comparative_sweep_20260706_233723.json`.

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

## Analog sweeps (Stages 4–5)

| Probe | Key result |
|-------|------------|
| κ survival sweep | mean_survival vs R **broad** on κ ∈ [0.80, 0.90]; best Δ% ~0.015% at κ≈0.891 |
| λt=2 PDE (κ=0.85) | mean_survival = **0.137606** (Δ 0.09% vs R) |
| Comparative sweep (fast) | hybrid scores **0.9989–0.9991** |
| Golden S¹ probe | packing coverage ≈ **0.889**; phase histograms in `outputs/golden_phase_hist_*.png` |

## Framing

**Compatible emergent signature** — not an exact identity, not forced by invariants, not contradicted by simulation.