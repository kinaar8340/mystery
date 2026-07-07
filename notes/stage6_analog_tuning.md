# Stage 6 — Analog Objective Tuning (July 2026)

Close-out note for the meta-optimizer analog objective: survival penalty at λt = 2, optional golden-angle reward, and dual-analog mode. Full numbers in [`docs/RESULTS.md`](../docs/RESULTS.md); live summary in the [HF Space](https://huggingface.co/spaces/kinaar111/mystery) under **Manual Edit → Stage 6 — Current Best & Robustness**.

---

## Objective

Base loss (island + Hopf + braiding) from `meta_optimize_invariants.py`, extended in `meta_optimize_phi_probe.py`:

```
loss = base_loss + w_s × survival_term + w_κ × (κ − κ_target)² − golden_reward
```

| Term | Definition |
|------|------------|
| `survival_term` | `hybrid_delta_pct / 100` when `--use-hybrid-objective`, else `\|mean_survival − R\|` |
| `kappa_prior_term` | `(κ − κ_target)²` when `--use-kappa-prior` (default κ_target = 0.85) |
| `golden_reward` | `weight × (0.5×golden_closeness + 0.5×S¹ packing)` when `--golden-angle-steps` (dual_analog only) |
| `R` | φ² + e² − π² ≈ **+0.137486** |

Three comparison modes with `--compare-baseline`:

| Mode | Flags |
|------|-------|
| **baseline** | Island + Hopf only |
| **survival_penalty** | `+ --use-survival-penalty --use-hybrid-objective` (no golden steps) |
| **dual_analog** | `+ --golden-angle-steps --golden-reward-weight 0.3` |
| **κ prior** (optional) | `--use-kappa-prior --kappa-prior-target 0.85 --kappa-prior-weight W` on survival/dual modes |

---

## Tuning timeline

| Run | Trials | w_s | Loss (dual) | κ | Δ% vs R | Hybrid | Notes |
|-----|--------|-----|-------------|---|---------|--------|-------|
| Pilot | 8 | 1 | 63.64 | 0.77 | 0.355% | 0.9987 | κ stuck at 0.77 |
| 30-trial | 30 | 5 | **56.98** | 0.89 | 0.121% | 0.9990 | Big improvement |
| 50-trial | 50 | 5 | **56.98** | 0.89 | 0.121% | 0.9990 | Identical to 30-trial |
| w_s sweep | 25 | 5–12 | **56.98** @ w_s=5 | 0.89 | 0.121% | 0.9990 | Stable; w_s=5 best loss |
| Robustness (std) | 18 grid | — | — | 0.89 | 0.121% | 0.9990 | IC/twist/λt/step modes |
| Robustness (expanded) | 70 grid | — | — | 0.89 | 0.121% | 0.9990 | 6 IC, 5 seeds, λt 1.5–2.5, twist 8–17.5 |
| κ prior w_κ=500 | 30 | 5 | 57.78 | 0.89 | 0.121% | 0.9990 | κ unchanged; dual > baseline |

**50-trial mode comparison (w_s = 5, no κ prior):**

| Mode | Loss | κ | mean_survival | Δ% vs R | hybrid | golden_reward |
|------|------|---|---------------|---------|--------|---------------|
| baseline | 57.22 | 0.89 | — | — | — | — |
| survival_penalty | 57.26 | 0.89 | 0.137651 | 0.121% | 0.9990 | — |
| dual_analog | **56.98** | 0.89 | 0.137651 | 0.121% | 0.9990 | 0.275 |

---

## Current best operating point

| Parameter | Value |
|-----------|-------|
| κ | **0.890** |
| W_g | **111.41** (wg_base = 350.0) |
| braiding_target | 0.798 |
| w_s | **5.0** |
| golden_reward_weight | 0.3 |
| mean_survival @ λt=2 | **0.137651** |
| Δ% vs R | **0.121%** |
| hybrid score | **0.9990** |
| dual_analog loss | **56.98** |

Loss breakdown (best dual-analog trial):

| Component | Value |
|-----------|-------|
| base_loss | 57.221 |
| survival_term | 0.00747 |
| w_s × survival_term | 0.0374 |
| golden_reward | 0.275 |
| final_loss | 56.983 |

---

## Key takeaways

1. **Raising w_s from 1 → 5 moved κ from 0.77 → 0.89**, halving distance to the documented target κ = 0.85 (|κ − 0.85|: 0.08 → 0.04). The optimum landed near the κ-survival sweep sweet spot (~0.891), not exactly at κ_doc.

2. **Survival alignment improved sharply:** Δ% vs R dropped from 0.355% (pilot) to **0.121%**; hybrid score rose to **0.9990**.

3. **Dual-analog wins on both axes:** lowest loss (golden_reward offsets survival penalty) while retaining the improved survival metrics. Synergy between dissipative survival (λt = 2) and golden-angle helix packing is stable, not fragile.

4. **Optimizer variance is low:** 30- and 50-trial runs produced identical best parameters; TPE converged by ~trial 22.

5. **w_s ∈ [5, 12] does not shift κ:** higher weights only inflate the survival penalty term (0.037 → 0.090 at w_s = 12) without pulling κ toward 0.85. **w_s = 5** remains optimal for dual-analog loss.

6. **Robustness is strong:** at fixed κ = 0.89, W_g = 111.41, mean_survival = 0.137651 and Δ% = 0.121% hold across 18 comparative-sweep configurations (uniform/hopfion/helical ICs; twist rates 10/12.5/15; linear vs golden steps; λt = 2).

7. **κ prior does not shift the optimum (Stage 7):** squared prior `(κ − 0.85)²` at w_κ ∈ {50, 500} leaves κ at **0.890**. Island+Hopf base_loss strongly prefers κ ≈ 0.89 (trial κ=0.85 → loss 58.62 vs κ=0.89 → 57.22 in baseline). Survival alignment is also best near κ ≈ 0.89. The prior only adds overhead: +0.80 to loss at w_κ=500 without moving κ.

---

## κ prior experiment (July 2026)

Attempt to pull κ toward documented κ_doc = 0.85 while keeping survival alignment.

```bash
python scripts/meta_optimize_phi_probe.py \
  --compare-baseline --trials 30 \
  --use-survival-penalty --use-hybrid-objective --survival-penalty-weight 5 \
  --golden-angle-steps --golden-reward-weight 0.3 \
  --use-kappa-prior --kappa-prior-target 0.85 --kappa-prior-weight 500
```

| w_κ | Mode | Loss | κ | w_κ×term | golden | Notes |
|-----|------|------|---|----------|--------|-------|
| 50 | survival/dual† | 57.06 | 0.89 | 0.08 | 0.275 | †bug: golden leaked to survival_penalty (fixed) |
| 500 | survival_penalty | **58.06** | 0.89 | 0.80 | — | 57.22 + 0.037 + 0.80 |
| 500 | dual_analog | **57.78** | 0.89 | 0.80 | 0.275 | no longer beats baseline (57.22) |
| — | dual (no prior) | **56.98** | 0.89 | — | 0.275 | **production best** |

**Why κ stays at 0.89:** three aligned pressures — (1) island+Hopf minimum at κ≈0.89, (2) PDE survival sweet spot at κ≈0.891 per κ-sweep, (3) κ_doc = 0.85 is only 4% away and not competitive on combined loss. Saving w_κ×term at κ=0.85 (~0.80) does not compensate for higher base_loss at κ=0.85.

**Bug fix:** `compare-baseline` now forces `golden_angle_steps=False` on survival_penalty so `--golden-angle-steps` applies only to dual_analog.

Loss breakdown (best dual-analog trial, w_κ=500):

| Component | Value |
|-----------|-------|
| base_loss | 57.221 |
| w_s × survival_term | 0.037 |
| w_κ × (κ − 0.85)² | 0.80 |
| golden_reward | 0.275 |
| final_loss | **57.78** |

| Artifact | Path |
|----------|------|
| w_κ=50 (bugged) | `outputs/meta_optimize_phi_probe_20260707_003033.json` |
| w_κ=500 (valid) | `outputs/meta_optimize_phi_probe_20260707_003333.json` |

---

## Commands & artifacts

```bash
# 30-trial tuning (reference run)
toe/venv/bin/python scripts/meta_optimize_phi_probe.py \
  --compare-baseline --trials 30 \
  --use-survival-penalty --golden-angle-steps \
  --golden-reward-weight 0.3 --use-hybrid-objective \
  --survival-penalty-weight 5

# 50-trial confirmation
toe/venv/bin/python scripts/meta_optimize_phi_probe.py \
  --compare-baseline --trials 50 \
  --use-survival-penalty --golden-angle-steps \
  --golden-reward-weight 0.3 --use-hybrid-objective \
  --survival-penalty-weight 5

# w_s sensitivity
toe/venv/bin/python scripts/w_s_sweep.py --weights 8 10 12 --trials 25

# Robustness at best point (standard 18-run grid)
toe/venv/bin/python scripts/analog_comparative_sweep.py --kappa 0.89 --wg-base 350.0

# Expanded robust grid (70 runs: 6 IC, 5 seeds, broader λt/twist)
toe/venv/bin/python scripts/analog_comparative_sweep.py --robust --kappa 0.89 --wg-base 350.0

# κ prior (optional — tested w_κ=500, does not shift κ)
python scripts/meta_optimize_phi_probe.py \
  --compare-baseline --trials 30 \
  --use-survival-penalty --use-hybrid-objective --survival-penalty-weight 5 \
  --golden-angle-steps --golden-reward-weight 0.3 \
  --use-kappa-prior --kappa-prior-target 0.85 --kappa-prior-weight 500
```

| Artifact | Path |
|----------|------|
| 30-trial JSON | `outputs/meta_optimize_phi_probe_20260706_231311.json` |
| 50-trial JSON | `outputs/meta_optimize_phi_probe_20260706_233925.json` |
| w_s sweep JSON | `outputs/w_s_sweep_20260706_233453.json` |
| Robustness JSON (18-run) | `outputs/analog_comparative_sweep_20260706_233723.json` |
| Robustness JSON (70-run) | `outputs/analog_comparative_sweep_20260707_012224.json` |
| κ prior w_κ=500 | `outputs/meta_optimize_phi_probe_20260707_003333.json` |

---

## Framing

**Compatible emergent signature** — the analog objective does not force an exact identity. It trades a small island-loss increase (+0.04 via survival term) for measurably better alignment with R at λt = 2. The converged κ ≈ 0.89 is consistent with the earlier κ-survival sweep (best Δ% vs R near κ ≈ 0.891), suggesting the model prefers the value that best balances PDE survival with Hopf/island constraints rather than the documented κ_doc = 0.85 alone.

**Production recommendation:** use **dual-analog** objective with **w_s = 5**, **golden_reward_weight = 0.3**, **hybrid survival term**, **no κ prior**, at **κ_sim ≈ 0.89**, W_g ≈ 111.41 (loss **56.98**). Keep **κ_doc = 0.85** for documentation and nulling formulas — see Stage 7 paired comparison in [`docs/RESULTS.md`](../docs/RESULTS.md).

---

## Open questions (Stage 7+)

| Question | Status / next step |
|----------|-------------------|
| Pull κ toward 0.85? | **Closed** — squared prior (w_κ≤500) and paired sweep confirm κ_sim ≈ 0.89; retain κ_doc=0.85 for docs |
| Is κ ≈ 0.89 preferred over κ_doc? | **Yes for simulation** — best Δ% vs R, island+Hopf minimum; κ_doc marginally better on uniform hybrid |
| golden_reward_weight sensitivity | Grid w_s × golden_reward_weight at fixed 30+ trials |
| 100+ trials | Diminishing returns given convergence by trial ~22 |

See also [`open_questions.md`](open_questions.md) and [`emergent_signatures.md`](emergent_signatures.md).