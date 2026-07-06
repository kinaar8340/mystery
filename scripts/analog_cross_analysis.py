#!/usr/bin/env python3
"""
analog_cross_analysis.py
========================
Stage 5 overlay: κ sweep, PDE survival, S¹ phase histograms, comparative sweep heatmap.
"""

from __future__ import annotations

import json
import subprocess
import sys
from glob import glob
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

DOCS_FIG = Path(__file__).resolve().parent.parent / "docs" / "figures"
R_RESIDUAL = PHI**2 + E**2 - PI**2
E_INV2 = float(np.exp(-2.0))
GOLDEN_FRACTION = 360.0 * (1.0 - 1.0 / PHI) / 1000.0


def _latest_json(pattern: str) -> dict | None:
    files = sorted(glob(pattern), reverse=True)
    if not files:
        return None
    return json.loads(Path(files[0]).read_text())


def _ensure_sweep_data() -> dict:
    data = _latest_json(str(OUTPUT_DIR / "kappa_survival_sweep_*.json"))
    if data is None:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "kappa_survival_sweep.py")],
            check=True,
        )
        data = _latest_json(str(OUTPUT_DIR / "kappa_survival_sweep_*.json"))
    return data or {}


def _ensure_comparative_data(fast: bool = True) -> dict:
    data = _latest_json(str(OUTPUT_DIR / "analog_comparative_sweep_*.json"))
    if data is None:
        cmd = [sys.executable, str(Path(__file__).parent / "analog_comparative_sweep.py")]
        if fast:
            cmd.append("--fast")
        subprocess.run(cmd, check=True)
        data = _latest_json(str(OUTPUT_DIR / "analog_comparative_sweep_*.json"))
    return data or {}


def build_overlay_figure(
    kappa_data: dict,
    comp_data: dict,
    out_path: Path,
) -> None:
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.28)

    # Panel A: κ sweep
    ax_a = fig.add_subplot(gs[0, 0])
    if kappa_data.get("sweep"):
        kappas = [r["kappa"] for r in kappa_data["sweep"]]
        surv = [r["mean_survival"] for r in kappa_data["sweep"]]
        ax_a.plot(kappas, surv, "o-", color="#2a9d8f", lw=2, ms=4)
        ax_a.axhline(R_RESIDUAL, color="#c9a227", ls="--", label=f"R={R_RESIDUAL:.4f}")
        ax_a.axhline(E_INV2, color="#6a4c93", ls=":", label=f"e⁻²={E_INV2:.4f}")
        ax_a.axhline(GOLDEN_FRACTION, color="#e76f51", ls="-.", label=f"golden/1000")
        ax_a.axvline(0.85, color="#888", ls="--", alpha=0.6)
        ax_a.set_xlabel("κ")
        ax_a.set_ylabel("mean_survival @ λt=2")
        ax_a.set_title("A · κ sweep (broad R alignment)")
        ax_a.legend(fontsize=7)
        ax_a.grid(alpha=0.3)

    # Panel B: PDE IC comparison at λt=2
    ax_b = fig.add_subplot(gs[0, 1])
    if comp_data.get("sweep"):
        pde_rows = [
            r for r in comp_data["sweep"]
            if r.get("subsystem") == "pde" and r.get("normalize_to_lambda_t") == 2.0
        ]
        if pde_rows:
            labels = [r["ic_type"] for r in pde_rows]
            vals = [r["mean_survival"] for r in pde_rows]
            colors = ["#2a6f97", "#6a4c93", "#e76f51"][: len(labels)]
            ax_b.bar(labels, vals, color=colors, alpha=0.85)
            ax_b.axhline(R_RESIDUAL, color="#c9a227", ls="--", lw=1.5)
            ax_b.axhline(E_INV2, color="#6a4c93", ls=":", lw=1.2)
            ax_b.set_ylabel("mean_survival")
            ax_b.set_title("B · PDE IC type @ λt=2")
            ax_b.grid(axis="y", alpha=0.3)

    # Panel C: conduit step_mode @ λt=2
    ax_c = fig.add_subplot(gs[1, 0])
    if comp_data.get("sweep"):
        cond = [
            r for r in comp_data["sweep"]
            if r.get("subsystem") == "conduit" and r.get("normalize_to_lambda_t") == 2.0
        ]
        if cond:
            labels = [f"{r['step_mode']}\nτ={r['twist_rate']}" for r in cond]
            hybrid = [r.get("hybrid_score", 0) for r in cond]
            packing = [r.get("packing_coverage", 0) for r in cond]
            x = np.arange(len(labels))
            w = 0.35
            ax_c.bar(x - w / 2, hybrid, w, label="hybrid score", color="#2a9d8f")
            ax_c.bar(x + w / 2, packing, w, label="S¹ packing", color="#c9a227")
            ax_c.set_xticks(x)
            ax_c.set_xticklabels(labels, fontsize=8)
            ax_c.set_title("C · Conduit golden vs linear @ λt=2")
            ax_c.legend(fontsize=8)
            ax_c.grid(axis="y", alpha=0.3)

    # Panel D: scatter hybrid vs Δ% R
    ax_d = fig.add_subplot(gs[1, 1])
    if comp_data.get("sweep"):
        pts = [r for r in comp_data["sweep"] if r.get("mean_survival") is not None]
        if pts:
            x = [r.get("delta_pct_vs_R", 0) for r in pts]
            y = [r.get("hybrid_score", 0) for r in pts]
            colors = [
                "#e76f51" if r.get("golden_angle_steps") else "#2a6f97"
                for r in pts
            ]
            ax_d.scatter(x, y, c=colors, alpha=0.75, s=40, edgecolors="#111", linewidths=0.3)
            ax_d.set_xlabel("Δ% vs R")
            ax_d.set_ylabel("hybrid score")
            ax_d.set_title("D · Sweep scatter (red=golden steps)")
            ax_d.grid(alpha=0.3)

    fig.suptitle(
        "Analog survival comparison — rotational (golden) + dissipative (e⁻²) @ λt=2",
        fontsize=12,
        y=0.98,
    )
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    kappa_data = _ensure_sweep_data()
    comp_data = _ensure_comparative_data(fast=True)

    out_path = OUTPUT_DIR / "analog_survival_comparison.png"
    build_overlay_figure(kappa_data, comp_data, out_path)
    DOCS_FIG.mkdir(parents=True, exist_ok=True)
    DOCS_FIG.joinpath("analog_survival_comparison.png").write_bytes(out_path.read_bytes())

    result = {
        "plot": str(out_path),
        "docs_plot": str(DOCS_FIG / "analog_survival_comparison.png"),
        "kappa_points": len(kappa_data.get("sweep", [])),
        "comparative_runs": comp_data.get("n_runs", 0),
    }
    report_path = save_report("analog_cross_analysis", result)
    print("=== Analog Cross Analysis (Stage 5) ===")
    print(f"Figure: {out_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())