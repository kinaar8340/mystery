# Variational Sketch — κ\* from Skyrme + Holonomy

Working note for open_questions.md §2. Algebraic null κ\* = e/π − R/π² is already known (`residual_kappa_sweep.py`). This document sketches the *derivation path* and testable predictions linking κ_doc, κ\*, and κ_sim.

---

## 1. Reduced holonomy action (ansatz)

After integrating out fast quaternion modes on the gauged Hopf lattice, define a slow holonomy angle θ(s) on the S¹ fiber with effective action:

```
S_eff[θ] = ∫ ds [ ½(θ̇ − ω_gauge(κ))² + (f₄/4) F_μν F^μν ] + S_Skyrme
```

| Term | Role |
|------|------|
| θ̇ − ω_gauge(κ) | Global pointer synchronization; κ sets holonomy damping |
| F_μν F^μν | Skyrme stabilizer on the slow sector |
| W_g = 350/π constraint | Fixes geometric winding (Hopf link target) |

**Gauge frequency ansatz:** ω_gauge(κ) = (e/π − κ) × (π/W_g) — holonomy gap between exponential drive scale e/π and locked pointer κ, normalized by the emergent winding quantum W_g.

---

## 2. Stationary condition → B(κ) — **derived**

Formal reduction: [`skyrme_holonomy_derivation.md`](skyrme_holonomy_derivation.md).

From mean-field free energy \(\mathcal{F}_0 = \frac{\kappa}{2}\bar\theta^2 - \Delta\omega\bar\theta\) (`Lagrangian_Derivation.pdf` §3) at Hopf fiber saturation \(\bar\theta \sim \pi\):

```
Φ_drive  = π · (e/π) = e
Φ_damp   = κ · π²
B(κ)     = π·Φ_drive − Φ_damp = π²(e/π − κ)
```

| Factor | Origin |
|--------|--------|
| **(e/π − κ)** | Holonomy gap: exponential drive ratio minus pointer damping |
| **π²** | Fiber half-turn π × quadratic gauge storage \(\frac{\kappa}{2}\bar\theta^2\) at \(\bar\theta \sim \pi\) |

Verify: `python scripts/skyrme_bound_derivation.py` → `outputs/skyrme_bound_derivation_*.json`.

**References:** `toe/papers/Lagrangian_Derivation.pdf`, `Relativistic_Completion.pdf`, `Observer_Synchronization.pdf`.

---

## 3. Exact null κ\*

Set the reduced mismatch equal to the Pythagorean residual R = φ² + e² − π²:

```
B(κ*) = R   ⟹   κ* = e/π − R/π² ≈ 0.8513
```

| κ | Value | |B(κ) − R| / R |
|---|-------|----------------|
| κ_doc | 0.8500 | ~9.5% |
| κ\* | 0.8513 | ~0% |
| κ_sim | ~0.890 | meta-opt + survival (not a B(κ) null) |

κ\* sits **0.16%** from κ_doc — the scaling thread is strong; exact identity at κ_doc is not claimed.

---

## 4. Why dynamics overshoot to κ_sim ≈ 0.89

The meta-optimizer minimizes **island + Hopf + braiding + survival**, not |B(κ) − R| alone:

```
L_total = L_island(κ) + 3·|W_g − wg_base/π| + 0.8·|braiding − target| + w_s·survival_term − golden_reward
```

**Updated interpretation (July 2026):** see [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md).

| Mechanism | Role in κ_sim selection |
|-----------|-------------------------|
| PDE survival @ λt=2 | **Primary** — Δ% vs R minimum near κ ≈ 0.891 |
| Conduit comparative sweep | Confirms κ_sim best Δ% (0.121% vs 0.166% @ κ_doc) |
| Island+Hopf base loss | **Nearly κ-flat** (~0.05 spread); weak braid_target co-tuning |
| vortex_369 κ_proxy | Readout shifts to ~0.885; κ_final stays near κ_doc under gentle braid gain |
| Holonomy-gap sign | κ_sim > e/π → damping-dominated regime (not B(κ) null) |

So κ_doc / κ\* / κ_sim form a **testable hierarchy**:

```
κ_doc  — static anchor (θ_crit, B(κ) framing, training seed)
κ*     — algebraic null B(κ) = R
κ_sim  — dynamic dissipative optimum (λ ≈ κ survival alignment)
```

Stage 7 paired sweep confirmed κ_sim wins on conduit Δ% vs R; κ_doc marginally wins on uniform PDE hybrid.

---

## 5. Falsification checklist

| Test | Confirms variational story | Weakens story |
|------|---------------------------|---------------|
| Topology bake grid drifts κ toward κ\* only with 369+toroidal on | Topology implements holonomy reduction | κ drift flat across flag grid |
| Meta-opt at island-only loss (no survival) → κ near κ\* or κ_doc | Survival term causes κ_sim overshoot | κ → 0.89 even without survival |
| Derive π² prefactor from reduced Skyrme action | **Done** — `skyrme_holonomy_derivation.md` | No π² term emerges |

---

## 6. Reproduce / extend

```bash
# Algebraic κ* (already done)
cd mystery && python scripts/residual_kappa_sweep.py

# Topology falsification (Stage 8)
cd mystery && ~/Projects/toe/venv/bin/python scripts/topology_kappa_bake_grid.py --bake-steps 500

# Magic island + braid gain (Stage 8b)
cd toe && venv/bin/python scripts/magic_island_sweep.py --topology-grid --island-z 129 --quick --braid-gains 0.002 0.005 0.01

# Island-only meta-opt ablation (future)
cd toe && venv/bin/python scripts/meta_optimize_invariants.py --trials 30
```

See also [`residual_scaling.md`](residual_scaling.md), [`stage6_analog_tuning.md`](stage6_analog_tuning.md), [`docs/RESULTS.md`](../docs/RESULTS.md).