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

## 2. Stationary condition → B(κ)

Minimize S_eff at fixed W_g under periodic boundary (toroidal_modulo9 when enabled):

```
δS/δθ = 0  ⟹  θ̇ = ω_gauge(κ)  (slow-mode lock)
```

The **effective mismatch energy** (one Fourier mode of the residual) scales as:

```
B(κ) = π² (e/π − κ)
```

- **π²** from S¹ × S¹ fiber Jacobian / winding-squared normalization (topological sector).
- **(e/π − κ)** from the holonomy gap between drive and damping.

This reproduces the postulated bound in `notes/residual_scaling.md` — the variational task is to derive the π² prefactor from the Skyrme reduction, not assume it.

**References:** `111_docs/toe/toe_swarm/papers/Lagrangian_Derivation.pdf`, `Observer_Synchronization.pdf`.

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

**Prediction:** ∂|B(κ) − R|/∂κ = 0 at κ\* under W_g constraint, but ∂L_total/∂κ = 0 shifts to κ_sim when:

1. Island loss has a secondary minimum near κ ≈ 0.89 (noble-gas stability targets).
2. PDE survival at λt=2 is best near κ ≈ 0.891 (κ survival sweep).
3. Golden-angle reward favors dual_analog without pulling κ back to κ_doc.

So κ_doc / κ\* / κ_sim form a **testable hierarchy**:

```
κ_doc  — documentation anchor (θ_crit, framing)
κ*     — variational null of B(κ) = R
κ_sim  — combined dynamics + survival optimum
```

Stage 7 paired sweep confirmed κ_sim wins on conduit Δ% vs R; κ_doc marginally wins on uniform PDE hybrid.

---

## 5. Falsification checklist

| Test | Confirms variational story | Weakens story |
|------|---------------------------|---------------|
| Topology bake grid drifts κ toward κ\* only with 369+toroidal on | Topology implements holonomy reduction | κ drift flat across flag grid |
| Meta-opt at island-only loss (no survival) → κ near κ\* or κ_doc | Survival term causes κ_sim overshoot | κ → 0.89 even without survival |
| Derive π² prefactor from reduced Skyrme action | B(κ) is derived, not fitted | No π² term emerges |

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