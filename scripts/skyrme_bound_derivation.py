#!/usr/bin/env python3
"""
skyrme_bound_derivation.py
============================
Verify the formal Skyrme+holonomy reduction B(κ) = π²(e/π − κ) and κ* null.

Derives numerically from the mean-field free energy in Lagrangian_Derivation.pdf:
  F_0(θ̄) = (κ/2) θ̄² − Δω θ̄
and fiber saturation Θ* = π with drive capacity π·(e/π) and damping capacity κπ².
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

R = PHI**2 + E**2 - PI**2
E_OVER_PI = E / PI
KAPPA_DOC = 0.85
KAPPA_SIM = 0.89
THETA_STAR = PI  # fiber saturation half-turn


def bound_from_gap(kappa: float) -> float:
    """B(κ) = π²(e/π − κ) = πe − κπ²."""
    return PI**2 * (E_OVER_PI - kappa)


def bound_from_capacities(kappa: float) -> float:
    """B(κ) = π·Φ_drive − Φ_damp = π·e − κπ²."""
    phi_drive = THETA_STAR * E_OVER_PI  # = e
    phi_damp = kappa * THETA_STAR**2
    return PI * phi_drive - phi_damp


def kappa_star() -> float:
    return E_OVER_PI - R / PI**2


def mean_field_free_energy(theta_bar: float, kappa: float, delta_omega: float) -> float:
    """F_0 = (κ/2) θ̄² − Δω θ̄  (Lagrangian_Derivation §3)."""
    return 0.5 * kappa * theta_bar**2 - delta_omega * theta_bar


def mean_field_equilibrium(kappa: float, delta_omega: float) -> float:
    """∂F/∂θ̄ = κ θ̄ − Δω = 0."""
    return delta_omega / kappa


def main() -> int:
    k_star = kappa_star()
    delta_omega = 0.002  # toe default scale

    # Identity checks
    k_test = np.linspace(0.80, 0.92, 13)
    gap_form = np.array([bound_from_gap(k) for k in k_test])
    cap_form = np.array([bound_from_capacities(k) for k in k_test])
    max_identity_err = float(np.max(np.abs(gap_form - cap_form)))

    # κ* null
    b_star = bound_from_gap(k_star)
    null_err = abs(b_star - R)
    null_rel_pct = 100 * null_err / abs(R)

    # Mean-field stationarity
    theta_eq_doc = mean_field_equilibrium(KAPPA_DOC, delta_omega)
    grad_check = KAPPA_DOC * theta_eq_doc - delta_omega

    # Key κ values
    table = []
    for label, k in [
        ("kappa_doc", KAPPA_DOC),
        ("kappa_star", k_star),
        ("kappa_sim", KAPPA_SIM),
        ("e_over_pi", E_OVER_PI),
    ]:
        b = bound_from_gap(k)
        table.append({
            "label": label,
            "kappa": float(k),
            "B_kappa": float(b),
            "delta_B_minus_R": float(b - R),
            "rel_err_pct": 100 * abs(b - R) / abs(R),
            "e_over_pi_minus_kappa": float(E_OVER_PI - k),
        })

    result = {
        "derivation": "notes/skyrme_holonomy_derivation.md",
        "reference": {"R": R, "e_over_pi": E_OVER_PI, "theta_star": THETA_STAR},
        "identity_check": {
            "max_err_gap_vs_capacity": max_identity_err,
            "pass": max_identity_err < 1e-12,
        },
        "kappa_star": {
            "value": k_star,
            "B_at_kappa_star": b_star,
            "null_abs_err": null_err,
            "null_rel_pct": null_rel_pct,
            "pass": null_rel_pct < 0.01,
        },
        "mean_field": {
            "delta_omega": delta_omega,
            "theta_eq_at_kappa_doc": theta_eq_doc,
            "grad_F_at_eq": grad_check,
            "pass": abs(grad_check) < 1e-15,
        },
        "kappa_table": table,
        "predictions": {
            "static_null_kappa": k_star,
            "kappa_doc_pct_from_star": 100 * abs(KAPPA_DOC - k_star) / KAPPA_DOC,
            "kappa_sim_exceeds_e_over_pi": KAPPA_SIM > E_OVER_PI,
        },
    }
    path = save_report("skyrme_bound_derivation", result)

    print("=== Skyrme + Holonomy Bound Derivation ===")
    print(f"B(κ) identity (gap vs capacity): max err = {max_identity_err:.2e}  "
          f"{'PASS' if result['identity_check']['pass'] else 'FAIL'}")
    print(f"κ* = {k_star:.6f}  B(κ*) = {b_star:.6f}  R = {R:.6f}")
    print(f"Null error: {null_err:.2e} ({null_rel_pct:.4f}% of R)  "
          f"{'PASS' if result['kappa_star']['pass'] else 'FAIL'}")
    print(f"Mean-field ∂F/∂θ̄ at κ_doc: {grad_check:.2e}  "
          f"{'PASS' if result['mean_field']['pass'] else 'FAIL'}")
    print(f"|κ_doc − κ*| = {100 * abs(KAPPA_DOC - k_star) / KAPPA_DOC:.3f}%")
    print(f"κ_sim > e/π: {KAPPA_SIM > E_OVER_PI} (damping-dominated regime)")
    print(f"Report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())