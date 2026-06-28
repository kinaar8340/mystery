#!/usr/bin/env python3
"""High-precision φ² + e² ≈ π² analysis and 30-60-90 comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, law_of_cosines_angle, save_report


def exact_30_60_90_ratios() -> dict:
    """Unit triangle with shortest side = 1."""
    a, b, c = 1.0, np.sqrt(3), 2.0
    return {
        "sides": [a, b, c],
        "angles_deg": {
            "opposite_1": law_of_cosines_angle(a, b, c),
            "opposite_sqrt3": law_of_cosines_angle(b, a, c),
            "opposite_2": law_of_cosines_angle(c, a, b),
        },
        "ratios_normalized": [1.0, float(np.sqrt(3)), 2.0],
    }


def phi_e_pi_triangle() -> dict:
    phi, e, pi = PHI, E, PI
    sides = sorted([phi, e, pi])
    s_min, s_mid, s_max = sides

    angles = {
        "opposite_phi": law_of_cosines_angle(phi, e, pi),
        "opposite_e": law_of_cosines_angle(e, phi, pi),
        "opposite_pi": law_of_cosines_angle(pi, phi, e),
    }

    pythag_check = phi**2 + e**2 - pi**2
    pythag_rel_err = abs(pythag_check) / pi**2

    ratios_norm_phi = [phi / phi, e / phi, pi / phi]
    exact = exact_30_60_90_ratios()
    ratio_deviation = [
        abs(ratios_norm_phi[i] - exact["ratios_normalized"][i]) / exact["ratios_normalized"][i]
        for i in range(3)
    ]

    return {
        "constants": {"phi": phi, "e": e, "pi": pi},
        "phi_squared": phi**2,
        "e_squared": e**2,
        "pi_squared": pi**2,
        "pythagorean_residual": pythag_check,
        "pythagorean_relative_error_pct": 100 * pythag_rel_err,
        "is_exact_pythagorean": abs(pythag_check) < 1e-12,
        "angles_deg": angles,
        "angles_369_tens": {
            "phi_angle_tens": angles["opposite_phi"] / 10,
            "e_angle_tens": angles["opposite_e"] / 10,
            "pi_angle_tens": angles["opposite_pi"] / 10,
        },
        "side_ratios_normalized_to_phi": ratios_norm_phi,
        "exact_30_60_90_ratios": exact["ratios_normalized"],
        "ratio_deviation_from_30_60_90_pct": [100 * d for d in ratio_deviation],
        "mean_ratio_deviation_pct": 100 * float(np.mean(ratio_deviation)),
    }


def plot_triangle_comparison(result: dict) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    labels = ["φ", "e", "π"]
    mystery_angles = [
        result["angles_deg"]["opposite_phi"],
        result["angles_deg"]["opposite_e"],
        result["angles_deg"]["opposite_pi"],
    ]
    exact_angles = [30.0, 60.0, 90.0]

    x = np.arange(3)
    w = 0.35
    axes[0].bar(x - w / 2, mystery_angles, w, label="φ-e-π triangle", color="#c9a227")
    axes[0].bar(x + w / 2, exact_angles, w, label="30-60-90 exact", color="#2a6f97", alpha=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    axes[0].set_ylabel("Angle (degrees)")
    axes[0].set_title("Angle comparison")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    ratios_m = result["side_ratios_normalized_to_phi"]
    ratios_e = result["exact_30_60_90_ratios"]
    axes[1].bar(x - w / 2, ratios_m, w, label="φ-e-π (norm to φ)", color="#c9a227")
    axes[1].bar(x + w / 2, ratios_e, w, label="30-60-90 exact", color="#2a6f97", alpha=0.8)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)
    axes[1].set_ylabel("Side ratio")
    axes[1].set_title("Normalized side ratios")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    fig.suptitle(
        f"φ² + e² − π² = {result['pythagorean_residual']:+.6f} "
        f"({result['pythagorean_relative_error_pct']:.2f}% rel. error)",
        fontsize=11,
    )
    fig.tight_layout()

    out = OUTPUT_DIR / "phi_e_pi_triangle.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    result = phi_e_pi_triangle()
    plot_path = plot_triangle_comparison(result)
    report_path = save_report("phi_e_pi_analysis", {**result, "plot": str(plot_path)})

    print("=== φ, e, π Triangle Analysis ===")
    print(f"φ² + e² − π² = {result['pythagorean_residual']:+.10f}")
    print(f"Relative error: {result['pythagorean_relative_error_pct']:.4f}%")
    print(f"Angles: φ→{result['angles_deg']['opposite_phi']:.3f}°  "
          f"e→{result['angles_deg']['opposite_e']:.3f}°  "
          f"π→{result['angles_deg']['opposite_pi']:.3f}°")
    print(f"3-6-9 tens: {result['angles_369_tens']['phi_angle_tens']:.2f}, "
          f"{result['angles_369_tens']['e_angle_tens']:.2f}, "
          f"{result['angles_369_tens']['pi_angle_tens']:.2f}")
    print(f"Mean ratio deviation from 30-60-90: {result['mean_ratio_deviation_pct']:.2f}%")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())