#!/usr/bin/env python3
"""
Numerical sweep: R = φ²+e²−π² vs bound B(κ) = π²(e/π − κ).
Finds κ* that nulls the bound and compares to documented κ = 0.85.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

R = PHI**2 + E**2 - PI**2
E_OVER_PI = E / PI
KAPPA_DOC = 0.85
W_G = 350.0 / PI


def bound(kappa: float) -> float:
    return PI**2 * (E_OVER_PI - kappa)


def kappa_star() -> float:
    """κ solving π²(e/π − κ) = R  →  κ* = e/π − R/π²."""
    return E_OVER_PI - R / PI**2


def sweep(kappas: np.ndarray) -> list[dict]:
    rows = []
    for k in kappas:
        b = bound(k)
        rows.append({
            "kappa": float(k),
            "bound_B": float(b),
            "residual_R": float(R),
            "delta_B_minus_R": float(b - R),
            "relative_error_pct": 100 * abs(b - R) / abs(R),
        })
    return rows


def plot_sweep(rows: list[dict], k_star: float, path: Path) -> None:
    k = [r["kappa"] for r in rows]
    b = [r["bound_B"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(k, b, label="B(κ) = π²(e/π − κ)", color="#2a6f97", lw=2)
    ax.axhline(R, color="#c9a227", ls="--", label=f"R = φ²+e²−π² = {R:.5f}")
    ax.axvline(KAPPA_DOC, color="#e63946", ls=":", label=f"κ_doc = {KAPPA_DOC}")
    ax.axvline(k_star, color="#457b9d", ls="-.", label=f"κ* = {k_star:.5f}")
    ax.set_xlabel("κ")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_title("Residual scaling: R vs π²(e/π−κ)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def effective_theory_note(k_star: float) -> str:
    b_doc = bound(KAPPA_DOC)
    return (
        f"At κ = κ* = e/π − R/π² ≈ {k_star:.5f}, the bound B(κ) equals R exactly. "
        f"Documented κ = {KAPPA_DOC} gives B = {b_doc:.5f} ({100*abs(b_doc-R)/R:.1f}% from R). "
        f"κ* is only {100*abs(k_star-KAPPA_DOC)/KAPPA_DOC:.2f}% from κ_doc — "
        "suggesting the holonomy gap (e/π−κ) may be tuned so π²×gap ≈ R in the effective reduction. "
        "This is a numerical consistency check, not a derived identity."
    )


def main() -> int:
    k_star = kappa_star()
    kappas = np.linspace(0.70, 0.95, 100)
    rows = sweep(kappas)
    best = min(rows, key=lambda r: r["relative_error_pct"])

    plot_path = OUTPUT_DIR / "residual_kappa_sweep.png"
    plot_sweep(rows, k_star, plot_path)

    payload = {
        "residual_R": float(R),
        "e_over_pi": float(E_OVER_PI),
        "kappa_documented": KAPPA_DOC,
        "kappa_star_exact": float(k_star),
        "kappa_star_formula": "e/π − R/π²",
        "bound_at_kappa_doc": float(bound(KAPPA_DOC)),
        "bound_at_kappa_star": float(bound(k_star)),
        "best_discrete_match": best,
        "W_g": float(W_G),
        "effective_theory_note": effective_theory_note(k_star),
        "plot": str(plot_path),
    }
    report_path = save_report("residual_kappa_sweep", payload)

    print("=== Residual κ Sweep ===")
    print(f"R = {R:+.8f}")
    print(f"κ* (exact null) = {k_star:.6f}  |  κ_doc = {KAPPA_DOC}  (Δ {100*abs(k_star-KAPPA_DOC)/KAPPA_DOC:.2f}%)")
    print(f"B(κ_doc) = {bound(KAPPA_DOC):.6f}  ({100*abs(bound(KAPPA_DOC)-R)/R:.1f}% from R)")
    print(f"Note: {payload['effective_theory_note'][:120]}...")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())