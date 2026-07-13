#!/usr/bin/env python3
"""Sweep κ at fixed λt=2; plot mean_survival vs κ with R, e^{-2}, golden analogs.

Uses flux_hopf_lib.simulation (not toe path hacks).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    E_INV2,
    GOLDEN_ANGLE_FRACTION,
    OUTPUT_DIR,
    R_RESIDUAL,
    save_report,
    simulate_twist_pde_survival,
)


def sweep_kappa(
    kappa_min: float = 0.80,
    kappa_max: float = 0.90,
    n_points: int = 23,
    lambda_t: float = 2.0,
    dt: float = 0.001,
    seed: int = 42,
    nx: int = 20,
    D: float = 0.05,
) -> dict:
    kappas = np.linspace(kappa_min, kappa_max, n_points)
    rows = []
    for kappa in kappas:
        result = simulate_twist_pde_survival(
            normalize_to_lambda_t=lambda_t,
            kappa=float(kappa),
            dt=dt,
            seed=seed,
            nx=nx,
            D=D,
        )
        mean_surv = result["survival"]["mean_survival"]
        comp = result["analog_comparisons"]["mean_survival"]
        rows.append({
            "kappa": float(kappa),
            "n_steps": result["normalization"]["n_steps"],
            "mean_survival": mean_surv,
            "hybrid_score": comp.get("hybrid_score", 0.0),
            "hybrid_delta_pct": comp.get("hybrid_delta_pct", 0.0),
            "delta_pct_vs_R": comp["delta_pct_vs_R"],
            "delta_pct_vs_e_inv2": comp["delta_pct_vs_e_inv2"],
            "delta_pct_vs_golden": comp.get("delta_pct_vs_golden", 0.0),
        })

    best = min(rows, key=lambda r: r["delta_pct_vs_R"])
    return {
        "lambda_t": lambda_t,
        "dt": dt,
        "nx": nx,
        "D": D,
        "seed": seed,
        "kappa_range": [kappa_min, kappa_max],
        "n_points": n_points,
        "source": "flux_hopf_lib.simulation",
        "reference": {
            "R": R_RESIDUAL,
            "e_inv2": E_INV2,
            "golden_angle_fraction": GOLDEN_ANGLE_FRACTION,
        },
        "rows": rows,
        "best_vs_R": best,
    }


def plot_sweep(data: dict, out_path: Path) -> None:
    rows = data["rows"]
    kappas = [r["kappa"] for r in rows]
    surv = [r["mean_survival"] for r in rows]
    ref = data["reference"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(kappas, surv, "o-", label="mean_survival", color="C0")
    ax.axhline(ref["R"], color="C1", ls="--", label=f"R ≈ {ref['R']:.4f}")
    ax.axhline(ref["e_inv2"], color="C2", ls="--", label=f"e⁻² ≈ {ref['e_inv2']:.4f}")
    ax.axhline(
        ref["golden_angle_fraction"],
        color="C3",
        ls=":",
        label=f"golden/1000 ≈ {ref['golden_angle_fraction']:.4f}",
    )
    best = data["best_vs_R"]
    ax.axvline(best["kappa"], color="gray", ls=":", alpha=0.7)
    ax.set_xlabel("κ")
    ax.set_ylabel("mean survival at λt = 2")
    ax.set_title("κ survival sweep (flux_hopf_lib)")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="κ survival sweep at λt=2")
    parser.add_argument("--kappa-min", type=float, default=0.80)
    parser.add_argument("--kappa-max", type=float, default=0.90)
    parser.add_argument("--n-points", type=int, default=23)
    parser.add_argument("--nx", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data = sweep_kappa(
        kappa_min=args.kappa_min,
        kappa_max=args.kappa_max,
        n_points=args.n_points,
        nx=args.nx,
        seed=args.seed,
    )
    plot_path = OUTPUT_DIR / "kappa_survival_sweep.png"
    plot_sweep(data, plot_path)
    report_path = save_report("kappa_survival_sweep", data)
    best = data["best_vs_R"]
    print(
        f"Best κ vs R: {best['kappa']:.4f}  "
        f"mean_survival={best['mean_survival']:.6f}  "
        f"Δ% vs R={best['delta_pct_vs_R']:.2f}%"
    )
    print(f"Wrote {plot_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
