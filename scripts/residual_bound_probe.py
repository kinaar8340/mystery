#!/usr/bin/env python3
"""
Explore bounds on φ²+e²−π² residual using W_g, κ, and braiding invariants.
Includes Kepler triangle contrast.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, PHI, PI, save_report

# Meta-optimizer best (June 2026)
KAPPA = 0.85
W_G = 350.0 / PI
WG_BASE = 351.5
PHI_B = 0.754


def pythag_residual() -> float:
    return PHI**2 + E**2 - PI**2


def kepler_triangle() -> dict:
    """Exact golden-ratio right triangle: 1 : √φ : φ."""
    a, b, c = 1.0, np.sqrt(PHI), PHI
    def ang(opp, s1, s2):
        return float(np.degrees(np.arccos(np.clip((s1**2 + s2**2 - opp**2) / (2*s1*s2), -1, 1))))
    return {
        "sides": [a, float(np.sqrt(PHI)), PHI],
        "angles_deg": [ang(a, b, c), ang(b, a, c), ang(c, a, b)],
        "is_exact_pythagorean": abs(a**2 + b**2 - c**2) < 1e-12,
        "note": "Exact within golden geometry — contrast to approximate φ-e-π triangle",
    }


def candidate_bounds(R: float) -> list[dict]:
    """Algebraic candidates linking residual to TOE invariants."""
    k = KAPPA
    wg = W_G
    phi_b = PHI_B
    e_over_pi = E / PI

    exprs = {
        "pi_squared_times_e_over_pi_minus_kappa": PI**2 * (e_over_pi - k),
        "pi_times_e_minus_kappa_pi_squared": PI * E - k * PI**2,
        "kappa_times_pi_minus_phi_squared": k * (PI - PHI**2),
        "phi_squared_over_pi_times_e_over_pi_minus_kappa": (PHI**2 / PI) * (e_over_pi - k),
        "braiding_times_pi_times_e_over_pi_minus_kappa": phi_b * PI * (e_over_pi - k),
        "R_over_Wg": R / wg,
        "R_times_Wg": R * wg,
        "kappa_minus_e_over_pi": k - e_over_pi,
        "pi_times_kappa_minus_e_over_pi_squared": PI * (k - e_over_pi) ** 2,
        "one_over_Wg_times_phi_squared": PHI**2 / wg,
        "theta_link_residual": (2 * PI * wg / (2 * wg + 1)) - PI,
        "wg_inv_times_pi_times_kappa_gap": (1 / wg) * PI * abs(e_over_pi - k),
    }
    rows = []
    for name, val in exprs.items():
        rows.append({
            "expression": name,
            "value": float(val),
            "residual_R": R,
            "delta_from_R": float(val - R),
            "relative_error_pct": 100 * abs(val - R) / abs(R) if R else 0,
        })
    rows.sort(key=lambda x: x["relative_error_pct"])
    return rows


def high_precision_residual() -> dict:
    """Check stability with extended precision via decimal."""
    from decimal import Decimal, getcontext
    getcontext().prec = 80
    phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
    e = Decimal(1).exp()
    pi = Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111757428215126593484743593850331058209749445923078164062862089986280348253421170679")
    R = float(phi**2 + e**2 - pi**2)
    R_float = pythag_residual()
    return {
        "residual_decimal": R,
        "residual_float64": R_float,
        "drift_float_vs_decimal": abs(R - R_float),
        "stable": abs(R - R_float) < 1e-10,
    }


def main() -> int:
    R = pythag_residual()
    bounds = candidate_bounds(R)
    hp = high_precision_residual()
    kepler = kepler_triangle()

    result = {
        "pythagorean_residual": R,
        "relative_error_on_pi_squared_pct": 100 * abs(R) / PI**2,
        "high_precision": hp,
        "kepler_triangle_contrast": kepler,
        "best_bound_candidates": bounds[:8],
        "leading_candidate": bounds[0],
        "interpretation": {
            "residual_status": "Small and stable; not zero. No exact invariant forces φ²+e²=π².",
            "best_algebraic_near_miss": (
                f"{bounds[0]['expression']} ≈ {bounds[0]['value']:.6f} "
                f"(Δ from R = {bounds[0]['delta_from_R']:+.6f}, "
                f"{bounds[0]['relative_error_pct']:.1f}% rel. err)"
            ),
            "kepler_contrast": (
                "Kepler triangle is exact in golden geometry; φ-e-π mixes three transcendental families."
            ),
            "physical_read": (
                "Near-alignment is compatible with Hopf/quaternion setting (π topology, e drive/damping, "
                "φ from pentagonal/Clifford projections) but not variationally forced at current precision."
            ),
        },
    }
    report_path = save_report("residual_bound_probe", result)

    print("=== Residual Bound Probe ===")
    print(f"R = φ²+e²−π² = {R:+.10f}  (stable: {hp['stable']})")
    print(f"Best bound: {bounds[0]['expression']} = {bounds[0]['value']:.6f}  "
          f"(Δ {bounds[0]['delta_from_R']:+.6f}, {bounds[0]['relative_error_pct']:.1f}%)")
    print(f"Kepler exact Pythagorean: {kepler['is_exact_pythagorean']}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())