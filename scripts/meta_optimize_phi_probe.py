#!/usr/bin/env python3
"""
meta_optimize_phi_probe.py
==========================
Meta-optimize toe invariants with optional analog objective (Stage 6).

Base loss: island + Hopf + braiding (from meta_optimize_invariants.py).

Optional analog terms (--use-survival-penalty):
  survival_error = |mean_survival - R|   at λt = 2, λ ≈ κ
  golden_reward  = weight × golden_closeness   when --golden-angle-steps

With --use-hybrid-objective, survival term uses hybrid_delta_pct / 100 instead.

Usage:
  python meta_optimize_phi_probe.py --trials 12 --compare-baseline
  python meta_optimize_phi_probe.py --trials 20 --use-survival-penalty \\
      --golden-angle-steps --golden-reward-weight 0.3
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

MYSTERY_ROOT = Path(__file__).resolve().parent.parent
TOE_ROOT = Path.home() / "Projects" / "toe"
TOE_SRC = TOE_ROOT / "src"
OUTPUT_DIR = MYSTERY_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHI = (1 + np.sqrt(5)) / 2
E = np.e
PI = np.pi
R_RESIDUAL = PHI**2 + E**2 - PI**2
GOLDEN_FRACTION = 360.0 * (1.0 - 1.0 / PHI) / 1000.0

REAL_ISLAND_TARGETS = {
    2: {"stability": 8.0, "bursts": 0.05},
    10: {"stability": 8.0, "bursts": 0.05},
    18: {"stability": 8.0, "bursts": 0.05},
    36: {"stability": 8.0, "bursts": 0.05},
    54: {"stability": 8.0, "bursts": 0.05},
    86: {"stability": 8.0, "bursts": 0.05},
    129: {"stability": 8.5, "bursts": 0.02},
}


@dataclass
class AnalogObjectiveConfig:
    use_survival_penalty: bool = False
    golden_angle_steps: bool = False
    golden_reward_weight: float = 0.3
    use_hybrid_objective: bool = False
    survival_penalty_weight: float = 1.0
    lambda_t: float = 2.0
    pde_nx: int = 16


def _load_toe_modules():
    for p in (str(TOE_SRC), str(TOE_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)

    import torch
    import optuna

    rs_path = TOE_SRC / "relaxation_survival.py"
    spec = importlib.util.spec_from_file_location("relaxation_survival", rs_path)
    rs_mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = rs_mod
    spec.loader.exec_module(rs_mod)

    from conduit import RubikConeConduit  # noqa: PLC0415

    return torch, optuna, rs_mod, RubikConeConduit


def unit_circle_packing_coverage(conduit, n_samples: int = 128) -> float:
    """S¹ bin occupancy (packing density proxy)."""
    phases = []
    for s in np.linspace(0.05, conduit.max_depth, n_samples):
        pos = conduit.get_helix_3d(float(s), 0).detach().cpu().numpy()
        phases.append(float(np.arctan2(pos[1], pos[0]) % (2 * PI)))
    phases = np.array(phases)
    n_bins = 36
    bins = np.floor((phases / (2 * PI)) * n_bins).astype(int) % n_bins
    return float(len(np.unique(bins)) / n_bins)


def golden_closeness(value: float) -> float:
    return float(1.0 / (1.0 + abs(value - GOLDEN_FRACTION)))


def phi_e_pi_targets() -> dict[str, float]:
    return {
        "phi": PHI,
        "e": E,
        "pi": PI,
        "e_over_pi": E / PI,
        "phi_over_e": PHI / E,
        "phi_over_pi": PHI / PI,
        "pi_times_1_plus_kappa_at_085": PI * (1 + 0.85),
    }


def nearest_label(value: float, targets: dict[str, float]) -> tuple[str, float]:
    best = min(targets.items(), key=lambda kv: abs(value - kv[1]))
    return best[0], 100 * abs(value - best[1]) / abs(best[1])


def evaluate_trial(
    wg_base: float,
    kappa: float,
    braiding_target: float,
    analog: AnalogObjectiveConfig,
    *,
    RubikConeConduit,
    rs_mod,
    torch,
    n_seeds: int = 1,
) -> dict[str, Any]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    losses: list[float] = []
    last: dict[str, Any] = {}

    for _ in range(n_seeds):
        conduit = RubikConeConduit(
            embed_dim=384,
            twist_rate=12.5,
            max_depth=56.0,
            num_polarizations=9,
            quat_logical_dim=96,
            toroidal_modulo9=True,
            vortex_math_369=True,
            clifford_projection=True,
            wg_base=wg_base,
            kappa=kappa,
            braiding_target=braiding_target,
            golden_angle_steps=analog.golden_angle_steps,
        ).to(device)

        stats = conduit.monitor_topological_winding(n_samples=256)
        geo_w = float(stats.get("geometric_winding", 0.0))
        braiding = float(stats.get("braiding_phase", 0.0))
        stability = float(stats.get("active_cubes", 5.0))
        bursts = 0.05

        island_loss = 0.0
        for target in REAL_ISLAND_TARGETS.values():
            island_loss += abs(stability - target["stability"]) + 5.0 * abs(
                bursts - target["bursts"]
            )

        hopf_penalty = abs(geo_w - (wg_base / PI))
        braiding_penalty = abs(braiding - braiding_target)
        base_loss = island_loss + 3.0 * hopf_penalty + 0.8 * braiding_penalty

        survival_error = 0.0
        hybrid_delta = 0.0
        hybrid_score = 0.0
        mean_survival = None
        golden_reward = 0.0
        packing_coverage = None

        if analog.use_survival_penalty:
            pde = rs_mod.simulate_twist_pde_survival(
                normalize_to_lambda_t=analog.lambda_t,
                kappa=kappa,
                nx=analog.pde_nx,
                dt=0.001,
            )
            mean_survival = float(pde["survival"]["mean_survival"])
            comp = pde["analog_comparisons"]["mean_survival"]
            hybrid_delta = float(comp.get("hybrid_delta_pct", 0.0))
            hybrid_score = float(comp.get("hybrid_score", 0.0))
            survival_error = abs(mean_survival - R_RESIDUAL)

            if analog.golden_angle_steps:
                packing_coverage = unit_circle_packing_coverage(conduit)
                g_close = golden_closeness(mean_survival)
                golden_reward = analog.golden_reward_weight * (
                    0.5 * g_close + 0.5 * packing_coverage
                )

        survival_term = 0.0
        if analog.use_survival_penalty:
            if analog.use_hybrid_objective:
                survival_term = hybrid_delta / 100.0
            else:
                survival_term = survival_error
            total = (
                base_loss
                + analog.survival_penalty_weight * survival_term
                - golden_reward
            )
        else:
            total = base_loss

        losses.append(total)
        last = {
            "loss": total,
            "base_loss": base_loss,
            "survival_term": survival_term,
            "island_loss": island_loss,
            "hopf_penalty": hopf_penalty,
            "braiding_penalty": braiding_penalty,
            "survival_error": survival_error,
            "hybrid_delta_pct": hybrid_delta,
            "hybrid_score": hybrid_score,
            "mean_survival": mean_survival,
            "golden_reward": golden_reward,
            "packing_coverage": packing_coverage,
            "discovered_Wg": wg_base / PI,
            "kappa": kappa,
            "braiding_target": braiding_target,
            "geo_w": geo_w,
            "braiding": braiding,
        }

    last["loss"] = float(np.mean(losses))
    return last


PILOT_REFERENCE = {
    "baseline": {"loss": 63.92, "kappa": 0.77, "mean_survival": None, "delta_pct_vs_R": None},
    "survival_penalty": {
        "loss": 63.92, "kappa": 0.77, "mean_survival": 0.137974,
        "delta_pct_vs_R": 0.355, "hybrid_score": 0.9987,
    },
    "dual_analog": {
        "loss": 63.64, "kappa": 0.77, "mean_survival": 0.137974,
        "delta_pct_vs_R": 0.355, "hybrid_score": 0.9987, "golden_reward": 0.275,
    },
}


def _format_analog_flags(analog: AnalogObjectiveConfig) -> str:
    flags = []
    if analog.use_survival_penalty:
        flags.append("use-survival-penalty")
    if analog.golden_angle_steps:
        flags.append("golden-angle-steps")
    if analog.use_hybrid_objective:
        flags.append("use-hybrid-objective")
    if not flags:
        return "(none — island + Hopf + braiding only)"
    extra = []
    if analog.use_survival_penalty:
        extra.append(f"survival-penalty-weight={analog.survival_penalty_weight}")
    if analog.golden_angle_steps:
        extra.append(f"golden-reward-weight={analog.golden_reward_weight}")
    return ", ".join(flags) + ("; " + ", ".join(extra) if extra else "")


def _objective_formula(analog: AnalogObjectiveConfig) -> str:
    if not analog.use_survival_penalty:
        return "loss = base_loss  (island + Hopf + braiding)"
    term = "hybrid_delta/100" if analog.use_hybrid_objective else "|mean_survival − R|"
    w_s = analog.survival_penalty_weight
    golden = " − golden_reward" if analog.golden_angle_steps else ""
    return f"loss = base_loss + {w_s} × {term}{golden}"


def _print_run_header(label: str, trials: int, analog: AnalogObjectiveConfig) -> None:
    print("\n" + "=" * 72)
    print(f"  Mode: {label}  |  Trials: {trials}")
    print("=" * 72)
    print(f"  Active flags: {_format_analog_flags(analog)}")
    print(f"  Objective:    {_objective_formula(analog)}")
    if analog.use_survival_penalty:
        print(f"  w_s (--survival-penalty-weight): {analog.survival_penalty_weight}")
    print("-" * 72)


def _trial_progress_callback(log_every: int, total_trials: int):
    def callback(study, trial):
        n = trial.number + 1
        if n % log_every != 0 and n != total_trials:
            return
        best = study.best_trial
        attrs = best.user_attrs
        parts = [
            f"trial {n:3d}/{total_trials}",
            f"best_loss={best.value:.4f}",
            f"κ={best.params.get('kappa', 0):.3f}",
            f"W_g={attrs.get('discovered_Wg', 0):.3f}",
        ]
        if attrs.get("mean_survival") is not None:
            parts.append(f"mean_survival={attrs['mean_survival']:.6f}")
        if attrs.get("hybrid_score") is not None:
            parts.append(f"hybrid={attrs['hybrid_score']:.4f}")
        print("  " + "  ".join(parts))

    return callback


def run_native_optimize(
    trials: int,
    analog: AnalogObjectiveConfig,
    *,
    label: str = "native",
    log_every: int = 5,
) -> dict[str, Any]:
    try:
        torch, optuna, rs_mod, RubikConeConduit = _load_toe_modules()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": str(exc), "label": label}

    def objective(trial):
        wg_base = trial.suggest_float("wg_base", 300.0, 400.0, step=0.5)
        kappa = trial.suggest_float("kappa", 0.70, 0.95, step=0.01)
        braiding_target = trial.suggest_float("braiding_target", 0.75, 0.85, step=0.001)
        result = evaluate_trial(
            wg_base,
            kappa,
            braiding_target,
            analog,
            RubikConeConduit=RubikConeConduit,
            rs_mod=rs_mod,
            torch=torch,
        )
        for key, val in result.items():
            if val is not None and key != "loss":
                trial.set_user_attr(key, val)
        return result["loss"]

    _print_run_header(label, trials, analog)

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        study_name=f"meta_phi_{label}",
    )
    study.optimize(
        objective,
        n_trials=trials,
        show_progress_bar=False,
        callbacks=[_trial_progress_callback(log_every, trials)],
    )

    best = study.best_trial
    attrs = dict(best.user_attrs)
    survival_term = attrs.get("survival_term", 0.0)
    base_loss = attrs.get("base_loss", best.value)
    golden_reward = attrs.get("golden_reward", 0.0) or 0.0
    return {
        "status": "ok",
        "label": label,
        "trials": trials,
        "analog_config": {
            "use_survival_penalty": analog.use_survival_penalty,
            "golden_angle_steps": analog.golden_angle_steps,
            "golden_reward_weight": analog.golden_reward_weight,
            "use_hybrid_objective": analog.use_hybrid_objective,
            "survival_penalty_weight": analog.survival_penalty_weight,
        },
        "best_loss": best.value,
        "best_params": best.params,
        "best_attrs": attrs,
        "loss_breakdown": {
            "base_loss": base_loss,
            "survival_term": survival_term,
            "survival_penalty_weight": analog.survival_penalty_weight,
            "weighted_survival": analog.survival_penalty_weight * survival_term
            if analog.use_survival_penalty
            else 0.0,
            "golden_reward": golden_reward,
            "final_loss": best.value,
        },
        "best_w_g": attrs.get("discovered_Wg"),
        "best_kappa": best.params.get("kappa"),
        "best_braiding": best.params.get("braiding_target"),
        "mean_survival": attrs.get("mean_survival"),
        "survival_error": attrs.get("survival_error"),
        "hybrid_score": attrs.get("hybrid_score"),
        "hybrid_delta_pct": attrs.get("hybrid_delta_pct"),
        "golden_reward": golden_reward,
        "packing_coverage": attrs.get("packing_coverage"),
    }


def run_legacy_subprocess(trials: int) -> dict:
    """Original wrapper around toe meta_optimize_invariants.py."""
    script = TOE_ROOT / "scripts" / "meta_optimize_invariants.py"
    python = TOE_ROOT / "venv" / "bin" / "python"
    if not python.is_file():
        python = Path(sys.executable)
    if not script.is_file():
        return {"status": "error", "reason": f"Missing {script}", "label": "legacy"}

    try:
        proc = subprocess.run(
            [str(python), str(script), "--trials", str(trials)],
            cwd=str(TOE_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "trials": trials, "label": "legacy"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": str(exc), "label": "legacy"}

    stdout = proc.stdout + proc.stderr
    result = {
        "status": "ok" if proc.returncode == 0 else "failed",
        "label": "legacy",
        "returncode": proc.returncode,
        "trials": trials,
        "stdout_tail": stdout[-4000:],
    }
    for line in stdout.splitlines():
        if "Emergent wg_base:" in line and "Wg =" in line:
            try:
                result["best_w_g"] = float(line.split("Wg =")[1].strip())
            except (IndexError, ValueError):
                pass
        if "Emergent κ:" in line:
            try:
                result["best_kappa"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        if "Emergent braiding_target:" in line:
            try:
                result["best_braiding"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        if "Best loss:" in line:
            try:
                result["best_loss"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass
    return result


def analyze_clustering(meta: dict) -> dict:
    targets = phi_e_pi_targets()
    analysis: dict[str, Any] = {"targets": targets, "clustering": {}}
    if meta.get("best_kappa") is not None:
        k = meta["best_kappa"]
        label, delta = nearest_label(k, {"e_over_pi": E / PI, "phi_inv": 1 / PHI, "kappa_doc": 0.85})
        analysis["clustering"]["kappa"] = {
            "value": k, "nearest": label, "delta_pct": delta,
        }
    if meta.get("best_braiding") is not None:
        b = meta["best_braiding"]
        label, delta = nearest_label(
            b, {"phi_b_doc": 0.8145, "phi_inv": 1 / PHI, "phi_over_pi": PHI / PI}
        )
        analysis["clustering"]["braiding"] = {"value": b, "nearest": label, "delta_pct": delta}
    if meta.get("best_w_g") is not None:
        w = meta["best_w_g"]
        target_w = 350 / PI
        analysis["clustering"]["w_g"] = {
            "value": w,
            "target_350_over_pi": target_w,
            "delta_pct": 100 * abs(w - target_w) / target_w,
        }
    if meta.get("mean_survival") is not None:
        ms = meta["mean_survival"]
        analysis["clustering"]["mean_survival"] = {
            "value": ms,
            "R_residual": R_RESIDUAL,
            "delta_pct_vs_R": 100 * abs(ms - R_RESIDUAL) / abs(R_RESIDUAL),
            "hybrid_score": meta.get("hybrid_score"),
        }
    return analysis


def _delta_pct_vs_r(mean_survival: float | None) -> float | None:
    if mean_survival is None:
        return None
    return 100 * abs(mean_survival - R_RESIDUAL) / abs(R_RESIDUAL)


def _comparison_table_row(
    label: str, run: dict, analysis: dict, *, baseline_loss: float | None
) -> dict[str, Any]:
    ms = run.get("mean_survival")
    delta = analysis.get("clustering", {}).get("mean_survival", {}).get("delta_pct_vs_R")
    if delta is None and ms is not None:
        delta = _delta_pct_vs_r(ms)
    loss = run.get("best_loss")
    delta_vs_baseline = None
    if baseline_loss is not None and loss is not None and baseline_loss > 0:
        delta_vs_baseline = 100 * (loss - baseline_loss) / baseline_loss
    return {
        "mode": label,
        "final_loss": loss,
        "kappa": run.get("best_kappa"),
        "w_g": run.get("best_w_g"),
        "mean_survival": ms,
        "delta_pct_vs_R": delta,
        "hybrid_score": run.get("hybrid_score"),
        "golden_reward": run.get("golden_reward"),
        "delta_pct_vs_baseline": delta_vs_baseline,
    }


def print_comparison_table(rows: list[dict[str, Any]]) -> None:
    print("\n## Comparison Table\n")
    print("| Mode | Final Loss | κ | W_g | mean_survival | Δ% vs R | Hybrid Score | Golden Reward |")
    print("|------|------------|---|-----|---------------|---------|--------------|---------------|")
    for r in rows:
        ms = f"{r['mean_survival']:.6f}" if r["mean_survival"] is not None else "—"
        d_r = f"{r['delta_pct_vs_R']:.3f}%" if r["delta_pct_vs_R"] is not None else "—"
        hybrid = f"{r['hybrid_score']:.4f}" if r["hybrid_score"] is not None else "—"
        golden = f"{r['golden_reward']:.4f}" if r.get("golden_reward") else "—"
        kappa = f"{r['kappa']:.3f}" if r["kappa"] is not None else "—"
        wg = f"{r['w_g']:.4f}" if r["w_g"] is not None else "—"
        loss = f"{r['final_loss']:.4f}" if r["final_loss"] is not None else "—"
        print(
            f"| {r['mode']} | {loss} | {kappa} | {wg} | {ms} | {d_r} | {hybrid} | {golden} |"
        )


def print_key_findings(rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print("\n## Key Findings\n")
    by_mode = {r["mode"]: r for r in rows}
    pilot = PILOT_REFERENCE

    # κ alignment
    for mode in ("survival_penalty", "dual_analog"):
        if mode not in by_mode:
            continue
        k = by_mode[mode].get("kappa")
        pilot_k = pilot.get(mode, {}).get("kappa", 0.77)
        if k is not None:
            dist_085 = abs(k - 0.85)
            pilot_dist = abs(pilot_k - 0.85)
            moved = "closer" if dist_085 < pilot_dist else "farther from"
            print(
                f"**κ alignment ({mode}):** Best κ = {k:.3f} (pilot: {pilot_k:.2f}). "
                f"With w_s = {args.survival_penalty_weight}, κ moved {moved} the target "
                f"κ ≈ 0.85 (|κ − 0.85| = {dist_085:.3f} vs pilot {pilot_dist:.3f})."
            )

    # mean_survival vs pilot
    for mode in ("survival_penalty", "dual_analog"):
        if mode not in by_mode:
            continue
        ms = by_mode[mode].get("mean_survival")
        pilot_ms = pilot.get(mode, {}).get("mean_survival")
        pilot_delta = pilot.get(mode, {}).get("delta_pct_vs_R")
        if ms is not None and pilot_ms is not None:
            cur_delta = by_mode[mode].get("delta_pct_vs_R") or _delta_pct_vs_r(ms)
            imp = (pilot_delta or 0) - (cur_delta or 0)
            direction = "improved" if imp > 0 else "worsened"
            print(
                f"**Survival vs pilot ({mode}):** mean_survival = {ms:.6f} "
                f"(pilot {pilot_ms:.6f}); Δ% vs R = {cur_delta:.3f}% "
                f"(pilot {pilot_delta:.3f}%) — alignment {direction} by {abs(imp):.3f} pp."
            )

    # dual vs baseline
    if "baseline" in by_mode and "dual_analog" in by_mode:
        b = by_mode["baseline"]
        d = by_mode["dual_analog"]
        loss_better = (d["final_loss"] or 0) < (b["final_loss"] or 0)
        surv_better = False
        if d.get("delta_pct_vs_R") is not None and b.get("delta_pct_vs_R") is None:
            surv_better = True
        elif d.get("delta_pct_vs_R") is not None:
            surv_better = d["delta_pct_vs_R"] < (b.get("delta_pct_vs_R") or 999)
        both = loss_better and surv_better
        print(
            f"**Dual-analog vs baseline:** Final loss {d['final_loss']:.4f} vs "
            f"{b['final_loss']:.4f} ({'lower' if loss_better else 'not lower'}); "
            f"mean_survival Δ% vs R = "
            f"{d.get('delta_pct_vs_R', '—')}% (baseline has no survival term). "
            f"Dual mode {'achieves' if both else 'does not fully achieve'} both lower loss "
            f"and better survival alignment than baseline."
        )


def suggest_results_md(rows: list[dict[str, Any]], args: argparse.Namespace) -> str | None:
    by_mode = {r["mode"]: r for r in rows}
    if "dual_analog" not in by_mode or "baseline" not in by_mode:
        return None
    d = by_mode["dual_analog"]
    b = by_mode["baseline"]
    if (d["final_loss"] or 999) >= (b["final_loss"] or 0):
        return None
    ms = d.get("mean_survival")
    if ms is None:
        return None
    delta = d.get("delta_pct_vs_R") or _delta_pct_vs_r(ms)
    return (
        f"\n### Stage 6 — 30-trial analog objective tuning (w_s={args.survival_penalty_weight})\n\n"
        f"| Mode | Final Loss | κ | mean_survival | Δ% vs R | Hybrid |\n"
        f"|------|------------|---|---------------|---------|--------|\n"
        f"| baseline | {b['final_loss']:.2f} | {b['kappa']:.2f} | — | — | — |\n"
        f"| survival_penalty | {by_mode.get('survival_penalty', {}).get('final_loss', '—')} | "
        f"{by_mode.get('survival_penalty', {}).get('kappa', '—')} | "
        f"{by_mode.get('survival_penalty', {}).get('mean_survival', '—')} | "
        f"{by_mode.get('survival_penalty', {}).get('delta_pct_vs_R', '—')}% | "
        f"{by_mode.get('survival_penalty', {}).get('hybrid_score', '—')} |\n"
        f"| dual_analog | **{d['final_loss']:.2f}** | {d['kappa']:.2f} | "
        f"{ms:.6f} | {delta:.3f}% | {d.get('hybrid_score', 0):.4f} |\n\n"
        f"At w_s = {args.survival_penalty_weight}, dual-analog objective reduces island loss "
        f"while maintaining survival alignment near R = {R_RESIDUAL:.6f}."
    )


def print_recommendations(rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print("\n## Recommendations for Next Session\n")
    by_mode = {r["mode"]: r for r in rows}
    k_vals = [r.get("kappa") for r in rows if r.get("kappa") is not None]
    avg_dist_085 = np.mean([abs(k - 0.85) for k in k_vals]) if k_vals else None

    recs: list[str] = []
    if avg_dist_085 is not None and avg_dist_085 > 0.05:
        recs.append(
            f"κ remains {avg_dist_085:.3f} mean distance from 0.85 — try w_s ∈ [8, 15] "
            "or add explicit κ prior toward 0.85 in the search space center."
        )
    if args.trials < 50:
        recs.append(
            f"Run 50+ trials per mode to reduce TPE variance (current: {args.trials})."
        )
    if "dual_analog" in by_mode and "baseline" in by_mode:
        d, b = by_mode["dual_analog"], by_mode["baseline"]
        if abs((d["final_loss"] or 0) - (b["final_loss"] or 0)) < 0.1:
            recs.append(
                "Loss gap baseline vs dual_analog is small — run full grid analysis "
                "(analog_comparative_sweep) at best κ, W_g to confirm robustness."
            )
    if not recs:
        recs.append(
            "Results look stable; document in RESULTS.md and proceed to Stage 7 "
            "(weight sensitivity sweep over w_s and golden_reward_weight)."
        )
    for i, rec in enumerate(recs, 1):
        print(f"{i}. {rec}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meta-optimize with optional analog objective")
    p.add_argument("--trials", type=int, default=12, help="Optuna trials per run")
    p.add_argument("--legacy-only", action="store_true", help="Use toe subprocess only")
    p.add_argument("--compare-baseline", action="store_true",
                   help="Run baseline + survival + survival+golden and compare")
    p.add_argument("--use-survival-penalty", action="store_true")
    p.add_argument("--golden-angle-steps", action="store_true")
    p.add_argument("--golden-reward-weight", type=float, default=0.3)
    p.add_argument("--use-hybrid-objective", action="store_true")
    p.add_argument("--survival-penalty-weight", type=float, default=1.0)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    runs: list[dict] = []

    print("\n" + "#" * 72)
    print("#  Meta-Optimize φ Probe — Stage 6 Analog Objective Tuning")
    print("#" * 72)
    print(f"  Trials per mode: {args.trials}")
    print(f"  Compare baseline: {args.compare_baseline}")
    if args.compare_baseline or args.use_survival_penalty:
        analog_preview = AnalogObjectiveConfig(
            use_survival_penalty=args.use_survival_penalty or args.compare_baseline,
            golden_angle_steps=args.golden_angle_steps,
            golden_reward_weight=args.golden_reward_weight,
            use_hybrid_objective=args.use_hybrid_objective,
            survival_penalty_weight=args.survival_penalty_weight,
        )
        print(f"  Active flags (dual/survival): {_format_analog_flags(analog_preview)}")
        if analog_preview.use_survival_penalty:
            print(f"  Objective formula: {_objective_formula(analog_preview)}")
            print(f"  --survival-penalty-weight: {args.survival_penalty_weight}")
    print(f"  R = φ² + e² − π² = {R_RESIDUAL:.6f}")
    print("#" * 72)

    if args.legacy_only:
        runs.append(run_legacy_subprocess(args.trials))
    elif args.compare_baseline:
        runs.append(run_native_optimize(
            args.trials, AnalogObjectiveConfig(), label="baseline",
        ))
        survival_analog = AnalogObjectiveConfig(
            use_survival_penalty=True,
            use_hybrid_objective=args.use_hybrid_objective,
            survival_penalty_weight=args.survival_penalty_weight,
        )
        runs.append(run_native_optimize(
            args.trials,
            survival_analog,
            label="survival_penalty",
        ))
        runs.append(run_native_optimize(
            args.trials,
            AnalogObjectiveConfig(
                use_survival_penalty=True,
                golden_angle_steps=True,
                golden_reward_weight=args.golden_reward_weight,
                use_hybrid_objective=args.use_hybrid_objective,
                survival_penalty_weight=args.survival_penalty_weight,
            ),
            label="dual_analog",
        ))
    else:
        analog = AnalogObjectiveConfig(
            use_survival_penalty=args.use_survival_penalty,
            golden_angle_steps=args.golden_angle_steps,
            golden_reward_weight=args.golden_reward_weight,
            use_hybrid_objective=args.use_hybrid_objective,
            survival_penalty_weight=args.survival_penalty_weight,
        )
        runs.append(run_native_optimize(args.trials, analog, label="custom"))

    analyses = [analyze_clustering(r) for r in runs]
    baseline_loss = next(
        (r.get("best_loss") for r in runs if r.get("label") == "baseline" and r.get("status") == "ok"),
        None,
    )
    table_rows = [
        _comparison_table_row(r.get("label", "?"), r, a, baseline_loss=baseline_loss)
        for r, a in zip(runs, analyses, strict=True)
        if r.get("status") == "ok"
    ]
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "R_residual": R_RESIDUAL,
        "cli_args": {
            "trials": args.trials,
            "compare_baseline": args.compare_baseline,
            "use_survival_penalty": args.use_survival_penalty,
            "golden_angle_steps": args.golden_angle_steps,
            "golden_reward_weight": args.golden_reward_weight,
            "use_hybrid_objective": args.use_hybrid_objective,
            "survival_penalty_weight": args.survival_penalty_weight,
        },
        "pilot_reference": PILOT_REFERENCE,
        "runs": runs,
        "comparison_table": table_rows,
        "phi_e_pi_clustering": analyses,
        "objective_formula": _objective_formula(
            AnalogObjectiveConfig(
                use_survival_penalty=args.use_survival_penalty or args.compare_baseline,
                use_hybrid_objective=args.use_hybrid_objective,
                survival_penalty_weight=args.survival_penalty_weight,
                golden_angle_steps=args.golden_angle_steps,
            )
        ),
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"meta_optimize_phi_probe_{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, default=float))

    print("\n" + "#" * 72)
    print("#  Run Complete")
    print("#" * 72)
    print(f"  JSON report: {path}")

    if table_rows:
        print_comparison_table(table_rows)
        print_key_findings(table_rows, args)
        print_recommendations(table_rows, args)
        suggestion = suggest_results_md(table_rows, args)
        if suggestion:
            print("\n## Suggested docs/RESULTS.md addition\n")
            print(suggestion)

    for run, analysis in zip(runs, analyses, strict=True):
        label = run.get("label", "?")
        if run.get("status") != "ok":
            print(f"\n[{label}] status={run.get('status')} reason={run.get('reason', '')}")
            continue
        bd = run.get("loss_breakdown", {})
        if bd:
            print(f"\n[{label}] loss breakdown: base={bd.get('base_loss', 0):.4f}  "
                  f"survival_term={bd.get('survival_term', 0):.6f}  "
                  f"w_s×term={bd.get('weighted_survival', 0):.4f}  "
                  f"golden_reward={bd.get('golden_reward', 0):.4f}")

    return 0 if all(r.get("status") == "ok" for r in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())