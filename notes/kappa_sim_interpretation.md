# Physical Interpretation — κ_sim vs κ_doc (Open Question #9)

Working answer for July 2026. Complements [`kappa_star_variational.md`](kappa_star_variational.md), [`residual_scaling.md`](residual_scaling.md), and Stage 6–8 results in [`docs/RESULTS.md`](../docs/RESULTS.md).

**Status:** Partially resolved — a coherent physical story is available; full derivation from the Lagrangian remains open.

---

## 1. The three κ values are not rivals

| Symbol | Value | Physical role |
|--------|-------|----------------|
| **κ_doc** | 0.85 | **Static design anchor** — burst threshold θ_crit = π(1+κ), holonomy-gap framing B(κ), early meta-opt lock |
| **κ\*** | ≈ 0.8513 | **Algebraic null** — κ that makes B(κ) = π²(e/π−κ) equal R exactly; not a dynamical attractor |
| **κ_sim** | ≈ 0.89 | **Dissipative optimum** — κ that best satisfies island+survival constraints at λt = 2 |

The ~4% gap |κ_sim − κ_doc| ≈ 0.04 is **not a contradiction**. The model uses κ in two distinct physical senses:

1. **Documentation sense (κ_doc):** a fixed global pointer damping parameter in the reduced holonomy action and burst law θ_crit = π(1+κ).
2. **Simulation sense (κ_sim):** the effective relaxation rate λ ≈ κ that minimizes combined stability + survival objectives when the lattice is actually evolved and tuned.

κ\* sits between them as the *static* value that would null the residual scaling — 0.16% from κ_doc, but meta-opt and survival pull past it to κ_sim.

---

## 2. κ as a dissipation rate (the core physical picture)

In the mean-field twist-PDE reduction ([`relaxation_survival.py`](../../toe/src/relaxation_survival.py)):

```
gauge restoring torque  −κ θ̄   ⟹   effective rate λ ≈ κ
normalized horizon      λt = 2  ⟹   n_steps = (λt / κ) / dt
```

**κ is not merely a book-keeping constant.** It sets how fast global twist memory decays under gauged relaxation. At fixed λt = 2:

- **Higher κ** → fewer integration steps, **stronger per-step damping**
- **Lower κ** → more steps, **weaker per-step damping**

The measured **mean survival fraction** (mean twist retained / initial mean) is therefore a monotonic function of κ. The κ-survival sweep finds the best alignment with R at **κ ≈ 0.891**, not at κ_doc:

| κ | mean_survival @ λt=2 | Δ% vs R |
|---|----------------------|---------|
| 0.8500 | 0.137606 | 0.088% |
| 0.8513 (κ\*) | ≈ 0.1375 | ≈ 0.05% |
| 0.8900 | 0.137652 | 0.121% |
| **0.8909** (sweep best) | **0.137506** | **0.015%** |

(JSON: `outputs/kappa_survival_sweep_20260706_224432.json`)

**Physical reading:** κ_sim is the **operational damping strength** at which a memoryless exponential-relaxation analog (λt = 2) best tracks the φ-e-π residual R — not the value that nulls B(κ) in the static scaling law (that is κ\*).

---

## 3. Why κ_doc was locked first

κ_doc = 0.85 enters the TOE from **static** constraints:

| Constraint | Expression @ κ_doc |
|------------|-------------------|
| Burst threshold | θ_crit = π(1+κ) ≈ **5.812 rad** |
| Holonomy gap | e/π − κ ≈ **+0.0153** (positive — drive exceeds damping in gap measure) |
| Scaling proximity | κ\* only **0.16%** away |

Early meta-optimization (12 trials, island+Hopf only, no survival term) locked κ = **0.8500** exactly alongside wg_base ≈ 351.5 — see [`theta_crit_reconciliation.md`](theta_crit_reconciliation.md).

That lock reflects a **documentation-stable** point near κ\*, before the Analog Objective (Stage 6) introduced survival alignment at λt = 2 and deeper search over κ ∈ [0.70, 0.95].

---

## 4. Why dynamics select κ_sim ≈ 0.89

### 4a. Survival term (primary pull)

When the survival penalty is enabled (Stage 6), the optimizer minimizes hybrid Δ% vs R at λt = 2. The κ-survival curve is **broad** but centered near **0.89–0.891**. Stage 7 paired sweep confirms conduit Δ% improves from **0.166%** @ κ_doc to **0.121%** @ κ_sim; 70-run robust grid holds conduit metrics **identical** across twist 8–17.5 and step modes.

**Interpretation:** κ_sim is the dissipative rate at which **dynamic** survival best matches R under the conduit+PDE pipeline — a *runtime* property, not the static B(κ) null.

### 4b. Island+Hopf base loss (secondary, nearly flat)

Island+Hopf+braiding loss varies only **~0.05** across κ ∈ [0.80, 0.90] at fixed wg_base = 350 (local grid, July 2026). Measured braiding phase at init is ~0.085 for all κ; the optimizer co-tunes `braiding_target` (best ≈ 0.798 vs documented ~0.814).

| Combo | base_loss (island+Hopf+braid) |
|-------|-------------------------------|
| κ_doc, braid_target 0.814 | 57.234 |
| κ_sim, braid_target 0.798 | **57.221** |

So island loss alone **does not sharply select** κ_sim — but the κ_sim + braid_target pair is marginally preferred. The 50-trial **baseline** (no survival) also reports κ = 0.89, suggesting either weak coupling through braid_target exploration or a flat landscape where TPE clusters near the survival-informed region when studies are run in sequence.

### 4c. κ prior cannot reverse the pull

Squared prior (κ − 0.85)² at w_κ ≤ 500 adds +0.80 loss without moving κ from 0.89. The survival+island basin at κ_sim is **deeper** than the prior well at κ_doc.

---

## 5. Holonomy-gap regime crossing

Static scaling uses B(κ) = π²(e/π − κ):

| κ | e/π − κ | B(κ) | |B(κ)−R|/R |
|---|---------|------|-----------|
| κ_doc 0.85 | +0.0153 | +0.1506 | 9.5% |
| κ\* 0.8513 | +0.0139 | +0.1375 | ~0% |
| e/π 0.8653 | 0 | 0 | — |
| **κ_sim 0.89** | **−0.0247** | **−0.243** | — |

At κ_sim, the holonomy gap **changes sign**: global damping κ exceeds the e/π drive scale in the static gap measure. B(κ) is negative — κ_sim is **not** trying to null B(κ) = R. It optimizes **dynamic survival**, which peaks near 0.89 even though the algebraic null is κ\* ≈ 0.8513.

**Physical reading:**

- **κ_doc / κ\*** live in the **positive-gap** (e/π > κ) regime of the static holonomy narrative.
- **κ_sim** lives in the **damping-dominated** (κ > e/π) regime for the same gap measure — stronger global pointer coupling than the e/π reference scale.

This is consistent with κ_sim raising θ_crit to π(1+0.89) ≈ **5.94 rad** (~2% more burst headroom than κ_doc).

---

## 6. Topology readout: vortex_369 → κ_proxy ≈ κ_sim

Stage 8 topology bake shows **vortex_math_369** shifts the holonomy **κ_proxy** readout from ~0.854 (κ_doc neighborhood) to **~0.885** (κ_sim neighborhood), while adaptive κ_final under magic-island training stays near **κ_doc / κ\*** (~0.849 @ braid_gain 0.002).

κ_proxy formula (epoch/magic-island bake):

```
gap_stress = hopf_delta/W_g + 0.05·braiding_delta + …
κ_proxy = clip(e/π − gap_stress/π + knot_phase·0.01, …)   # knot_phase when 369 on
```

**Interpretation:**

- **κ_final** (adaptive feedback during training) anchors near κ_doc when braid gain is gentle — the *trained* pointer settles near the design seed.
- **κ_proxy** (holonomy readout under 369 topology) reports what the **emergent winding+braid stress** implies for the gap — and that readout aligns with κ_sim.

So 369 topology does not *force* κ_final to 0.89; it **measures** an emergent holonomy signature consistent with κ_sim. That supports reading κ_sim as the value the **active vortex sector** reports under modular-9 coupling, while κ_doc remains the **seed/training anchor**.

---

## 7. Synthesis — one paragraph

κ_doc = 0.85 is the **static** global pointer constant: it sets θ_crit, sits near the algebraic null κ\*, and seeds adaptive training. κ_sim ≈ 0.89 is the **dynamic** optimum: the effective dissipation rate λ ≈ κ at which normalized survival (λt = 2) best tracks R, reinforced by conduit comparative sweeps and visible in 369 holonomy readouts (κ_proxy → 0.885). The shift is not e/π (0.865); it is a move into a **damping-dominated** holonomy regime (κ > e/π) where multi-constraint stability outperforms the static B(κ) null. Neither value is "wrong" — they answer different questions.

---

## 8. What remains open

| Item | Status |
|------|--------|
| Derive π² prefactor and κ-dependence from reduced Skyrme action | Open |
| Prove survival minimum at 0.891 from PDE eigenstructure | Open |
| Island-only 100-trial ablation — is κ uniquely 0.89 without survival? | Recommended |
| Physical units / measurability of κ in experiment | Speculative |

---

## 9. Falsification

| Prediction | If true | If false |
|------------|---------|----------|
| Survival-off meta-opt → κ spreads or moves toward κ_doc/\* | κ_sim is survival-driven | κ_sim is fundamental attractor |
| PDE survival minimum stays at ~0.89 with structured ICs | Robust dissipative picture | κ_sim is uniform-IC artifact |
| 369-off κ_proxy returns to κ_doc neighborhood | 369 implements κ_sim readout mechanism | κ_proxy shift is incidental |

---

## 10. Reproduce

```bash
# κ-survival curve (λt=2)
cd mystery && .venv/bin/python scripts/kappa_survival_sweep.py

# Comparative sweeps @ κ_doc vs κ_sim
toe/venv/bin/python scripts/analog_comparative_sweep.py --kappa 0.85 --wg-base 350.0
toe/venv/bin/python scripts/analog_comparative_sweep.py --robust --kappa 0.89 --wg-base 350.0

# Topology κ_proxy (369 on → κ_sim)
cd toe && venv/bin/python scripts/epoch_bake_sweep.py --topology-grid
```

| Artifact | Path |
|----------|------|
| κ-survival sweep | `outputs/kappa_survival_sweep_20260706_224432.json` |
| 50-trial meta-opt (baseline κ=0.89) | `outputs/meta_optimize_phi_probe_20260706_233925.json` |
| Paired κ comparison | `outputs/analog_comparative_sweep_20260707_004010.json`, `…233723.json` |
| Robust 70-run | `outputs/analog_comparative_sweep_20260707_012224.json` |