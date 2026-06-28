#!/usr/bin/env python3
"""Bridge φ, e, π ratios to Aaron TOE locked invariants (κ, W_g, θ_crit, φ_b)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, PHI, PI, law_of_cosines_angle, save_report

# Locked / documented TOE values (see ~/Projects/toe and 111_docs/toe papers)
KAPPA_DOC = 0.85
WG_BASE = 350.0
W_G = WG_BASE / PI  # ≈ 111.408
PHI_B = 0.8145
THETA_CRIT_PDE = 5.8  # rad, burst sink in pde_relaxation.py


def theta_crit_from_wg(w_g: float) -> float:
    """Documented S³ burst formula: Θ_crit = 2π · W_g / (2W_g + 1)."""
    return 2 * PI * w_g / (2 * w_g + 1)


def relative_delta(a: float, b: float) -> float:
    return 100 * abs(a - b) / abs(b)


def bridge_analysis() -> dict:
    e_over_pi = E / PI
    pi_over_e = PI / E
    phi_over_e = PHI / E
    phi_over_pi = PHI / PI
    phi_sq_plus_e_sq = PHI**2 + E**2
    pythag_residual = phi_sq_plus_e_sq - PI**2

    theta_crit_formula = theta_crit_from_wg(W_G)

    comparisons = {
        "kappa_vs_e_over_pi": {
            "kappa_documented": KAPPA_DOC,
            "e_over_pi": e_over_pi,
            "delta_pct": relative_delta(KAPPA_DOC, e_over_pi),
            "note": "Global holonomy damping κ ≈ 0.85 vs e/π ≈ 0.865",
        },
        "w_g_lock": {
            "w_g": W_G,
            "wg_base": WG_BASE,
            "formula": "350 / π",
            "pi_enters_explicitly": True,
        },
        "theta_crit_reconciled": {
            "theta_link_rad": theta_crit_formula,
            "theta_link_deg": np.degrees(theta_crit_formula),
            "theta_link_note": "Hopf linking: 2π·W_g/(2W_g+1) ≈ π — NOT 5.8",
            "theta_crit_pde_rad": THETA_CRIT_PDE,
            "theta_crit_formula_rad": PI * (1 + KAPPA_DOC),
            "theta_crit_formula": "π(1+κ) with κ≈0.85",
            "pde_deg": np.degrees(THETA_CRIT_PDE),
            "note": "Reconciled in GW_Burst_Threshold.pdf (June 2026 revision)",
        },
        "phi_b_braiding": {
            "phi_b_documented": PHI_B,
            "phi_inverse": 1 / PHI,
            "phi_squared_inverse": 1 / PHI**2,
            "delta_from_phi_inv_pct": relative_delta(PHI_B, 1 / PHI),
        },
        "transcendental_ratios": {
            "phi_over_e": phi_over_e,
            "phi_over_pi": phi_over_pi,
            "e_over_pi": e_over_pi,
            "pi_over_e": pi_over_e,
            "phi_sq_plus_e_sq": phi_sq_plus_e_sq,
            "pi_squared": PI**2,
            "pythag_residual": pythag_residual,
        },
        "emerald_constant": {
            "phi_times_w_g": PHI * W_G,
            "note": "See toe/src/emeraldSunConduit.py: φ × 111.408 harmonic",
        },
        "damping_timescale": {
            "example": "δΘ(t) = δΘ(0) exp(−κt)",
            "half_life_at_kappa": np.log(2) / KAPPA_DOC,
            "half_life_at_e_over_pi": np.log(2) / e_over_pi,
        },
    }

    # Rank interesting near-misses
    near_misses = [
        ("κ vs e/π", relative_delta(KAPPA_DOC, e_over_pi)),
        ("φ⁻¹ vs φ_b", relative_delta(1 / PHI, PHI_B)),
        ("φ²+e² vs π² (Pythag)", 100 * abs(pythag_residual) / PI**2),
        ("30° vs angle(φ)", relative_delta(30.0, law_of_cosines_angle(PHI, E, PI))),
    ]

    return {
        "comparisons": comparisons,
        "near_miss_ranking_pct": sorted(
            [{"pair": k, "delta_pct": v} for k, v in near_misses], key=lambda x: x["delta_pct"]
        ),
    }


def main() -> int:
    result = bridge_analysis()
    report_path = save_report("hopf_constant_bridge", result)

    kappa_cmp = result["comparisons"]["kappa_vs_e_over_pi"]
    wg = result["comparisons"]["w_g_lock"]
    print("=== Hopf Constant Bridge ===")
    print(f"W_g = {wg['wg_base']}/π = {wg['w_g']:.6f}")
    print(f"κ = {kappa_cmp['kappa_documented']:.4f}  |  e/π = {kappa_cmp['e_over_pi']:.6f}  "
          f"(Δ {kappa_cmp['delta_pct']:.2f}%)")
    print(f"φ_b = {result['comparisons']['phi_b_braiding']['phi_b_documented']:.4f}  |  "
          f"φ⁻¹ = {result['comparisons']['phi_b_braiding']['phi_inverse']:.4f}")
    theta = result["comparisons"]["theta_crit_reconciled"]
    print(f"Θ_link = {theta['theta_link_rad']:.4f} rad (≈π)  |  "
          f"θ_crit = π(1+κ) = {theta['theta_crit_formula_rad']:.4f} rad  |  "
          f"PDE default = {theta['theta_crit_pde_rad']:.2f} rad")
    print(f"Pythag residual φ²+e²−π² = {result['comparisons']['transcendental_ratios']['pythag_residual']:+.6f}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())