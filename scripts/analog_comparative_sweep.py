#!/usr/bin/env python3
"""
analog_comparative_sweep.py
===========================
Grid sweep over twist_rate, IC type, λt normalization, and step mode (linear vs golden).

Prioritizes synergy runs: golden-angle steps + normalize_to_lambda_t = 2 together.
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

TOE_SRC = Path.home() / "Projects" / "toe" / "src"
R_RESIDUAL = PHI**2 + E**2 - PI**2
E_INV2 = float(np.exp(-2.0))
GOLDEN_ANGLE_DEG = 360.0 * (1.0 - 1.0 / PHI)
GOLDEN_FRACTION = GOLDEN_ANGLE_DEG / 1000.0
BRAIDING_TARGET = 0.8145
KAPPA = 0.85


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    for p in (str(path.parent), str(path.parent.parent)):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec.loader.exec_module(mod)
    return mod


def _ic_uniform(nx: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(0.1, 2.0, (nx, nx, nx))


def _ic_hopfion(nx: int) -> np.ndarray:
    lin = np.linspace(0, 2 * PI, nx, endpoint=False)
    x, y, z = np.meshgrid(lin, lin, lin, indexing="ij")
    r2 = (x - PI) ** 2 + (y - PI) ** 2 + (z - PI) ** 2
    return 0.2 + 2.5 * np.exp(-r2 / (2 * 0.35**2))


def _ic_helical(nx: int, kappa: float = KAPPA) -> np.ndarray:
    lin = np.linspace(0, 2 * PI, nx, endpoint=False)
    x, y, z = np.meshgrid(lin, lin, lin, indexing="ij")
    cw = 1.2 * np.sin(2.0 * x + 0.5 * z)
    ccw = 1.2 * np.sin(2.0 * x - 0.5 * z)
    theta_crit = PI * (1 + kappa)
    return np.clip(0.3 + cw + ccw, 0.1, theta_crit - 0.1)


def _ic_hopfion_blob(nx: int, kappa: float = KAPPA) -> np.ndarray:
    lin = np.linspace(0, 2 * PI, nx, endpoint=False)
    x, y, z = np.meshgrid(lin, lin, lin, indexing="ij")
    r2 = (x - PI) ** 2 + (y - PI) ** 2 + (z - PI) ** 2
    theta_crit = PI * (1 + kappa)
    return np.clip(0.2 + 2.5 * np.exp(-r2 / (2 * 0.35**2)), 0.1, theta_crit - 0.05)


def _ic_two_gyro(nx: int, kappa: float = KAPPA) -> np.ndarray:
    lin = np.linspace(0, 2 * PI, nx, endpoint=False)
    x, y, z = np.meshgrid(lin, lin, lin, indexing="ij")
    cw = 1.2 * np.sin(2.0 * x + 0.5 * z)
    ccw = 1.2 * np.sin(2.0 * x - 0.5 * z)
    theta_crit = PI * (1 + kappa)
    return np.clip(0.3 + cw + ccw, 0.1, theta_crit - 0.1)


def _ic_combined(nx: int, kappa: float = KAPPA) -> np.ndarray:
    blob = _ic_hopfion_blob(nx, kappa=kappa)
    gyro = _ic_two_gyro(nx, kappa=kappa)
    theta_crit = PI * (1 + kappa)
    return np.clip(blob + 0.4 * (gyro - 0.3), 0.1, theta_crit - 0.05)


def _ic_builders(kappa: float) -> dict[str, Callable[[int, int], np.ndarray]]:
    return {
        "uniform": lambda nx, seed: _ic_uniform(nx, seed),
        "hopfion": lambda nx, seed: _ic_hopfion(nx),
        "helical": lambda nx, seed: _ic_helical(nx, kappa=kappa),
        "hopfion_blob": lambda nx, seed: _ic_hopfion_blob(nx, kappa=kappa),
        "two_gyro": lambda nx, seed: _ic_two_gyro(nx, kappa=kappa),
        "combined": lambda nx, seed: _ic_combined(nx, kappa=kappa),
    }


def simulate_pde_case(
    ic_type: str,
    normalize_to_lambda_t: float | None,
    kappa: float = KAPPA,
    wg_base: float = 350.0,
    dt: float = 0.001,
    seed: int = 42,
    nx: int = 16,
) -> dict[str, Any]:
    rs = _load_module("relaxation_survival", TOE_SRC / "relaxation_survival.py")
    theta0 = _ic_builders(kappa)[ic_type](nx, seed)
    theta0_mean = float(theta0.mean())

    if normalize_to_lambda_t is not None:
        nt = rs.steps_for_lambda_t(normalize_to_lambda_t, kappa, dt)
    else:
        nt = 3000

    theta_crit = PI * (1.0 + kappa)
    D, delta_omega = 0.05, 0.002
    theta = theta0.copy()
    for _ in range(nt):
        lap = (
            np.roll(theta, 1, 0) + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1) + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2) + np.roll(theta, -1, 2) - 6 * theta
        ) / (1.0 / nx) ** 2
        bar_theta = float(theta.mean())
        gauge = -kappa * bar_theta
        burst = np.where(theta > theta_crit, -50.0 * (theta - theta_crit), 0.0)
        theta += dt * (D * lap + delta_omega + gauge + burst)
        theta = np.clip(theta, 0.01, 2 * PI - 0.01)

    mean_survival = float(theta.mean() / theta0_mean) if abs(theta0_mean) > 1e-12 else 0.0
    comp = rs.compare_to_analogs(mean_survival, f"pde_{ic_type}")
    return {
        "subsystem": "pde",
        "kappa": kappa,
        "wg_base": wg_base,
        "W_g": wg_base / PI,
        "ic_type": ic_type,
        "seed": seed,
        "normalize_to_lambda_t": normalize_to_lambda_t,
        "n_steps": nt,
        "mean_survival": mean_survival,
        "field_std": float(theta.std()),
        "delta_pct_vs_R": comp["delta_pct_vs_R"],
        "hybrid_score": comp["hybrid_score"],
        "hybrid_delta_pct": comp["hybrid_delta_pct"],
        "braiding_residual": None,
        "packing_coverage": None,
        "stability_score": float(1.0 / (1.0 + theta.std())),
    }


def unit_circle_phases(conduit, n_samples: int = 256) -> np.ndarray:
    """S¹ phases from helix XY projection (radians, wrapped)."""
    import torch

    s_vals = np.linspace(0.05, conduit.max_depth, n_samples)
    phases = []
    for s in s_vals:
        pos = conduit.get_helix_3d(float(s), 0).detach().cpu().numpy()
        phases.append(float(np.arctan2(pos[1], pos[0]) % (2 * PI)))
    return np.array(phases)


def packing_coverage(phases: np.ndarray, n_bins: int = 36) -> float:
    """Fraction of unit-circle bins occupied (0–1 packing density proxy)."""
    bins = np.floor((phases / (2 * PI)) * n_bins).astype(int) % n_bins
    occupied = len(np.unique(bins))
    return float(occupied / n_bins)


def simulate_conduit_case(
    twist_rate: float,
    step_mode: str,
    normalize_to_lambda_t: float | None,
    kappa: float = KAPPA,
    wg_base: float = 350.0,
    dt: float = 0.001,
    n_samples: int = 128,
) -> dict[str, Any]:
    try:
        import torch  # noqa: F401
    except ImportError:
        return {"subsystem": "conduit", "status": "skipped", "reason": "no torch"}

    mod = _load_module("toe_conduit", TOE_SRC / "conduit.py")
    RubikConeConduit = mod.RubikConeConduit
    golden = step_mode == "golden"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    conduit = RubikConeConduit(
        twist_rate=twist_rate,
        wg_base=wg_base,
        kappa=kappa,
        braiding_target=BRAIDING_TARGET,
        toroidal_modulo9=True,
        vortex_math_369=True,
        golden_angle_steps=golden,
    ).to(device)

    stats = conduit.monitor_topological_winding(n_samples=n_samples)
    braiding = float(stats.get("braiding_phase", 0.0))
    braiding_residual = abs(braiding - BRAIDING_TARGET)

    phases = unit_circle_phases(conduit, n_samples)
    coverage = packing_coverage(phases)

    rs = _load_module("relaxation_survival", TOE_SRC / "relaxation_survival.py")
    n_steps = (
        rs.steps_for_lambda_t(normalize_to_lambda_t, kappa, dt)
        if normalize_to_lambda_t is not None
        else 0
    )
    twist_result = rs.evolve_gauged_twist_survival(
        n_steps=0,
        kappa=kappa,
        normalize_to_lambda_t=normalize_to_lambda_t,
        dt=dt,
    )

    if normalize_to_lambda_t is not None:
        pde_surv = rs.simulate_twist_pde_survival(
            normalize_to_lambda_t=normalize_to_lambda_t,
            kappa=kappa,
            dt=dt,
            nx=16,
        )
        mean_survival = float(pde_surv["survival"]["mean_survival"])
        comp = pde_surv["analog_comparisons"]["mean_survival"]
    else:
        mean_survival = float(twist_result.get("identity_survival", 1.0))
        comp = rs.compare_to_analogs(
            twist_result.get("identity_residual", 0.0), "conduit_identity_residual"
        )

    stability = float(stats.get("active_cubes", 1)) * coverage / (1.0 + braiding_residual)

    return {
        "subsystem": "conduit",
        "kappa": kappa,
        "wg_base": wg_base,
        "W_g": wg_base / PI,
        "twist_rate": twist_rate,
        "step_mode": step_mode,
        "golden_angle_steps": golden,
        "normalize_to_lambda_t": normalize_to_lambda_t,
        "n_steps": n_steps,
        "mean_survival": mean_survival,
        "identity_survival": twist_result.get("identity_survival"),
        "identity_residual": twist_result.get("identity_residual"),
        "field_std": None,
        "delta_pct_vs_R": comp["delta_pct_vs_R"],
        "hybrid_score": comp["hybrid_score"],
        "hybrid_delta_pct": comp["hybrid_delta_pct"],
        "braiding_residual": braiding_residual,
        "packing_coverage": coverage,
        "stability_score": stability,
        "geometric_winding": float(stats.get("geometric_winding", 0.0)),
    }


def run_grid(
    *,
    kappa: float = KAPPA,
    wg_base: float = 350.0,
    twist_rates: tuple[float, ...] = (10.0, 12.5, 15.0),
    ic_types: tuple[str, ...] = ("uniform", "hopfion", "helical"),
    lambda_t_values: tuple[float | None, ...] = (None, 2.0),
    step_modes: tuple[str, ...] = ("linear", "golden"),
    seeds: tuple[int, ...] = (42,),
    fast: bool = False,
    robust: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if robust:
        ic_types = ("uniform", "hopfion", "helical", "hopfion_blob", "two_gyro", "combined")
        lambda_t_values = (None, 1.5, 2.0, 2.5)
        twist_rates = (8.0, 10.0, 12.5, 15.0, 17.5)
        seeds = (42, 7, 123, 99, 2026)

    for ic_type, lambda_t in itertools.product(ic_types, lambda_t_values):
        ic_seeds = seeds if ic_type == "uniform" else (42,)
        for seed in ic_seeds:
            rows.append(
                simulate_pde_case(
                    ic_type, lambda_t, kappa=kappa, wg_base=wg_base, seed=seed
                )
            )

    conduit_rates = (12.5,) if fast else twist_rates
    conduit_lts = (2.0,) if fast else (lt for lt in lambda_t_values if lt is not None)
    conduit_modes = step_modes

    for twist_rate, lambda_t, mode in itertools.product(
        conduit_rates, conduit_lts, conduit_modes
    ):
        rows.append(
            simulate_conduit_case(
                twist_rate, mode, lambda_t, kappa=kappa, wg_base=wg_base
            )
        )

    return rows


def summarize_robustness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Δ% vs R and hybrid across λt=2 runs."""
    lt2 = [r for r in rows if r.get("normalize_to_lambda_t") == 2.0]
    pde_lt2 = [r for r in lt2 if r.get("subsystem") == "pde"]
    conduit_lt2 = [r for r in lt2 if r.get("subsystem") == "conduit"]

    def _stats(group: list[dict]) -> dict[str, float]:
        if not group:
            return {}
        deltas = [r["delta_pct_vs_R"] for r in group if r.get("delta_pct_vs_R") is not None]
        hybrids = [r["hybrid_score"] for r in group if r.get("hybrid_score") is not None]
        survs = [r["mean_survival"] for r in group if r.get("mean_survival") is not None]
        return {
            "n": len(group),
            "delta_pct_min": float(min(deltas)),
            "delta_pct_max": float(max(deltas)),
            "delta_pct_mean": float(np.mean(deltas)),
            "delta_pct_std": float(np.std(deltas)),
            "hybrid_min": float(min(hybrids)),
            "hybrid_max": float(max(hybrids)),
            "hybrid_mean": float(np.mean(hybrids)),
            "mean_survival_min": float(min(survs)),
            "mean_survival_max": float(max(survs)),
            "mean_survival_mean": float(np.mean(survs)),
        }

    best = min(lt2, key=lambda r: r.get("delta_pct_vs_R", 999), default={})
    return {
        "lambda_t_2": {
            "all": _stats(lt2),
            "pde": _stats(pde_lt2),
            "conduit": _stats(conduit_lt2),
        },
        "best_at_lambda_t_2": best,
    }


def rank_synergy(rows: list[dict]) -> list[dict]:
    """Runs with golden + λt=2, sorted by hybrid score."""
    synergy = [
        r for r in rows
        if r.get("golden_angle_steps") and r.get("normalize_to_lambda_t") == 2.0
    ]
    pde_synergy = [
        r for r in rows
        if r.get("subsystem") == "pde" and r.get("normalize_to_lambda_t") == 2.0
    ]
    combined = synergy + pde_synergy
    return sorted(combined, key=lambda r: (-r.get("hybrid_score", 0), r.get("delta_pct_vs_R", 999)))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Analog comparative sweep")
    parser.add_argument("--fast", action="store_true", help="Reduced grid for quick test")
    parser.add_argument(
        "--robust",
        action="store_true",
        help="Expanded grid: 6 IC types, 5 uniform seeds, λt∈{1.5,2,2.5}, twist 8–17.5",
    )
    parser.add_argument("--kappa", type=float, default=KAPPA, help="κ for PDE/conduit runs")
    parser.add_argument(
        "--wg-base",
        type=float,
        default=350.0,
        help="wg_base (W_g = wg_base/π; 350 → W_g≈111.41)",
    )
    args = parser.parse_args()

    rows = run_grid(
        kappa=args.kappa, wg_base=args.wg_base, fast=args.fast, robust=args.robust
    )
    synergy = rank_synergy(rows)
    best_overall = min(
        [r for r in rows if r.get("mean_survival") is not None],
        key=lambda r: r.get("delta_pct_vs_R", 999),
        default={},
    )
    robustness = summarize_robustness(rows) if args.robust else None

    result = {
        "reference": {"R": R_RESIDUAL, "e_inv2": E_INV2, "golden_fraction": GOLDEN_FRACTION},
        "kappa": args.kappa,
        "wg_base": args.wg_base,
        "W_g": args.wg_base / PI,
        "robust_mode": args.robust,
        "n_runs": len(rows),
        "sweep": rows,
        "synergy_ranked": synergy[:10],
        "best_delta_vs_R": best_overall,
    }
    if robustness is not None:
        result["robustness_summary"] = robustness
    report_path = save_report("analog_comparative_sweep", result)

    print("=== Analog Comparative Sweep ===")
    print(f"Mode: {'robust' if args.robust else 'standard'}{' (fast)' if args.fast else ''}")
    print(f"Runs: {len(rows)}")
    if best_overall:
        print(f"Best vs R: {best_overall.get('subsystem')} "
              f"Δ%={best_overall.get('delta_pct_vs_R', 0):.3f}% "
              f"hybrid={best_overall.get('hybrid_score', 0):.4f}")
    if synergy:
        top = synergy[0]
        packing = top.get("packing_coverage")
        packing_s = f"{packing:.3f}" if packing is not None else "n/a"
        print(f"Top synergy (golden+λt=2): subsystem={top.get('subsystem')} "
              f"twist_rate={top.get('twist_rate')} ic={top.get('ic_type')} "
              f"packing={packing_s} hybrid={top.get('hybrid_score', 0):.4f}")
    if robustness:
        all_s = robustness["lambda_t_2"]["all"]
        if all_s:
            print(
                f"λt=2 robustness: Δ% vs R {all_s['delta_pct_min']:.3f}–"
                f"{all_s['delta_pct_max']:.3f}% (mean {all_s['delta_pct_mean']:.3f}%), "
                f"hybrid {all_s['hybrid_min']:.4f}–{all_s['hybrid_max']:.4f}"
            )
        best_lt2 = robustness.get("best_at_lambda_t_2") or {}
        if best_lt2:
            print(
                f"Best @ λt=2: {best_lt2.get('subsystem')} "
                f"ic={best_lt2.get('ic_type')} twist={best_lt2.get('twist_rate')} "
                f"Δ%={best_lt2.get('delta_pct_vs_R', 0):.3f}% "
                f"hybrid={best_lt2.get('hybrid_score', 0):.4f}"
            )
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())