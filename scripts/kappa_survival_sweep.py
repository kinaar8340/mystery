#!/usr/bin/env python3
"""Sweep κ at fixed λt=2; plot mean_survival vs κ with R, e^{-2}, golden analogs."""

from __future__ import annotations

import argparse
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
    nx: int = 20,
    D: float = 0.05,
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
        "reference": {
            "R": R_RESIDUAL,
            "e_inv2": E_INV2,
            "golden_fraction": GOLDEN_FRACTION,
            "kappa_doc": 0.85,
        },
        "sweep": rows,
        "best_vs_R": best,
    }


def plot_sweep(data: dict, out_path: Path, title_suffix: str = "") -> None:
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
    ax.set_title(f"PDE mean survival vs κ (λt = 2{title_suffix})")
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="κ survival sweep at λt=2")
    p.add_argument("--nx", type=int, default=20, help="Grid resolution (default 20)")
    p.add_argument("--D", type=float, default=0.05, help="Diffusion coefficient")
    p.add_argument("--kappa-min", type=float, default=0.80)
    p.add_argument("--kappa-max", type=float, default=0.90)
    p.add_argument("--n-points", type=int, default=23)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--report-name",
        type=str,
        default="",
        help="JSON report base name (default kappa_survival_sweep or kappa_survival_sweep_nx{N})",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    # Finer grids shift κ* toward κ_doc — widen range for nx >= 32
    kappa_min = args.kappa_min
    kappa_max = args.kappa_max
    if args.nx >= 32 and kappa_min >= 0.80 and kappa_max <= 0.90:
        kappa_min, kappa_max = 0.78, 0.92

    data = sweep_kappa(
        kappa_min=kappa_min,
        kappa_max=kappa_max,
        n_points=args.n_points,
        seed=args.seed,
        nx=args.nx,
        D=args.D,
    )
    suffix = f", nx={args.nx}, D={args.D}"
    report_base = args.report_name or (
        "kappa_survival_sweep" if args.nx == 20 else f"kappa_survival_sweep_nx{args.nx}"
    )
    plot_name = "kappa_survival_sweep.png" if args.nx == 20 else f"kappa_survival_sweep_nx{args.nx}.png"

    plot_path = OUTPUT_DIR / plot_name
    plot_sweep(data, plot_path, title_suffix=suffix)

    docs_dir = Path(__file__).resolve().parent.parent / "docs" / "figures"
    docs_dir.mkdir(parents=True, exist_ok=True)
    docs_plot = docs_dir / plot_name
    docs_plot.write_bytes(plot_path.read_bytes())

    report_path = save_report(report_base, {**data, "plot": str(plot_path)})

    best = data["best_vs_R"]
    k085 = min(data["sweep"], key=lambda r: abs(r["kappa"] - 0.85))

    print(f"=== κ Survival Sweep (λt = 2, nx={args.nx}, D={args.D}) ===")
    print(f"κ range: [{kappa_min:.3f}, {kappa_max:.3f}]  n={args.n_points}")
    print(f"At κ=0.85: mean_survival={k085['mean_survival']:.6f}  Δ% vs R={k085['delta_pct_vs_R']:.3f}%")
    print(f"Best vs R: κ={best['kappa']:.4f}  mean_survival={best['mean_survival']:.6f}  "
          f"Δ%={best['delta_pct_vs_R']:.4f}%")
    print(f"Plot: {plot_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())