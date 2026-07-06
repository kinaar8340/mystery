#!/usr/bin/env python3
"""Sweep κ ∈ [0.80, 0.90] at fixed λt=2; plot mean_survival vs κ with R, e^{-2}, golden analogs."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

TOE_SRC = Path.home() / "Projects" / "toe" / "src"
R_RESIDUAL = PHI**2 + E**2 - PI**2
E_INV2 = float(np.exp(-2.0))
GOLDEN_FRACTION = 360.0 * (1.0 - 1.0 / PHI) / 1000.0


def _load_relaxation_survival():
    path = TOE_SRC / "relaxation_survival.py"
    spec = importlib.util.spec_from_file_location("relaxation_survival", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sweep_kappa(
    kappa_min: float = 0.80,
    kappa_max: float = 0.90,
    n_points: int = 23,
    lambda_t: float = 2.0,
    dt: float = 0.001,
    seed: int = 42,
) -> dict:
    rs = _load_relaxation_survival()
    kappas = np.linspace(kappa_min, kappa_max, n_points)
    rows = []
    for kappa in kappas:
        result = rs.simulate_twist_pde_survival(
            normalize_to_lambda_t=lambda_t,
            kappa=float(kappa),
            dt=dt,
            seed=seed,
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
        "kappa_range": [kappa_min, kappa_max],
        "reference": {
            "R": R_RESIDUAL,
            "e_inv2": E_INV2,
            "golden_fraction": GOLDEN_FRACTION,
            "kappa_doc": 0.85,
        },
        "sweep": rows,
        "best_vs_R": best,
    }


def plot_sweep(data: dict, out_path: Path) -> None:
    kappas = [r["kappa"] for r in data["sweep"]]
    mean_surv = [r["mean_survival"] for r in data["sweep"]]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    ax = axes[0]
    ax.plot(kappas, mean_surv, "o-", color="#2a9d8f", lw=2, markersize=5, label="mean_survival (PDE)")
    ax.axhline(R_RESIDUAL, color="#c9a227", ls="--", lw=1.5, label=f"R = {R_RESIDUAL:.6f}")
    ax.axhline(E_INV2, color="#6a4c93", ls=":", lw=1.5, label=f"e⁻² = {E_INV2:.6f}")
    ax.axhline(GOLDEN_FRACTION, color="#e76f51", ls="-.", lw=1.5,
               label=f"golden/1000 = {GOLDEN_FRACTION:.6f}")
    ax.axvline(0.85, color="#888888", ls="--", alpha=0.7, label="κ_doc = 0.85")
    ax.set_xlabel("κ (gauge damping)")
    ax.set_ylabel("mean_survival at λt = 2")
    ax.set_title("PDE mean survival vs κ (fixed λt = 2)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax2 = axes[1]
    delta_r = [r["delta_pct_vs_R"] for r in data["sweep"]]
    hybrid = [r["hybrid_delta_pct"] for r in data["sweep"]]
    ax2.plot(kappas, delta_r, "s-", color="#c9a227", label="Δ% vs R")
    ax2.plot(kappas, hybrid, "^-", color="#2a6f97", label="hybrid Δ% (60% golden + 40% e⁻²)")
    ax2.axvline(0.85, color="#888888", ls="--", alpha=0.7)
    ax2.set_xlabel("κ")
    ax2.set_ylabel("Δ%")
    ax2.set_title("Alignment sensitivity to κ")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    data = sweep_kappa()
    plot_path = OUTPUT_DIR / "kappa_survival_sweep.png"
    plot_sweep(data, plot_path)
    docs_path = Path(__file__).resolve().parent.parent / "docs" / "figures" / "kappa_survival_sweep.png"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_bytes(plot_path.read_bytes())

    report_path = save_report("kappa_survival_sweep", {**data, "plot": str(plot_path)})

    best = data["best_vs_R"]
    k085 = min(data["sweep"], key=lambda r: abs(r["kappa"] - 0.85))

    print("=== κ Survival Sweep (λt = 2) ===")
    print(f"At κ=0.85: mean_survival={k085['mean_survival']:.6f}  Δ% vs R={k085['delta_pct_vs_R']:.3f}%")
    print(f"Best vs R: κ={best['kappa']:.4f}  mean_survival={best['mean_survival']:.6f}")
    print(f"Plot: {plot_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())