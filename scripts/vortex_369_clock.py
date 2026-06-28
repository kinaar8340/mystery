#!/usr/bin/env python3
"""3-6-9 positional geometry: clock angles, Rodin mod-9, and φ-e-π alignment."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, law_of_cosines_angle, save_report


def digital_root(n: int) -> int:
    """Rodin-style digital root (0 maps to 9 for cycling display)."""
    if n == 0:
        return 9
    r = n % 9
    return 9 if r == 0 else r


def rodin_doubling_cycle(length: int = 20) -> list[int]:
    """Powers of 2 mod 9 — avoids 3, 6, 9."""
    return [digital_root(2**k) for k in range(length)]


def clock_positions() -> dict:
    """Hour-hand angles: 12 o'clock = 0°, each hour = 30°."""
    positions = {}
    for hour in range(1, 13):
        angle = (hour * 30) % 360
        dr = digital_root(hour) if hour < 10 else digital_root(sum(int(d) for d in str(hour)))
        positions[hour] = {"angle_deg": angle, "digital_root": dr}
    return positions


def map_angles_to_369_tens() -> dict:
    phi_angle = law_of_cosines_angle(PHI, E, PI)
    e_angle = law_of_cosines_angle(E, PHI, PI)
    pi_angle = law_of_cosines_angle(PI, PHI, E)

    def classify(angle: float) -> dict:
        tens = angle / 10.0
        nearest_369 = min([3, 6, 9], key=lambda x: abs(tens - x))
        return {
            "angle_deg": angle,
            "tens_unit": tens,
            "nearest_369": nearest_369,
            "delta_from_nearest_369_tens": tens - nearest_369,
        }

    return {
        "phi": classify(phi_angle),
        "e": classify(e_angle),
        "pi": classify(pi_angle),
        "exact_30_60_90": {
            "30_deg": {"tens_unit": 3.0, "nearest_369": 3},
            "60_deg": {"tens_unit": 6.0, "nearest_369": 6},
            "90_deg": {"tens_unit": 9.0, "nearest_369": 9},
        },
    }


def plot_clock_and_rodin(mapping: dict) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Clock dial
    ax = axes[0]
    ax.set_aspect("equal")
    circle = plt.Circle((0, 0), 1, fill=False, color="#333")
    ax.add_patch(circle)
    for hour in range(1, 13):
        angle_rad = np.radians(90 - hour * 30)
        x, y = np.cos(angle_rad), np.sin(angle_rad)
        dr = digital_root(hour) if hour <= 9 else digital_root(sum(int(d) for d in str(hour)))
        color = "#e63946" if dr in (3, 6, 9) else "#457b9d"
        ax.plot([0, x], [0, y], color=color, alpha=0.4, lw=0.8)
        ax.text(1.08 * x, 1.08 * y, str(hour), ha="center", va="center", fontsize=9, color=color)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_title("Clock positions (30°/hour)\nred = digital root 3,6,9")
    ax.axis("off")

    # Rodin doubling cycle
    ax2 = axes[1]
    cycle = rodin_doubling_cycle(24)
    xs = np.arange(len(cycle))
    colors = ["#e63946" if v in (3, 6, 9) else "#1d3557" for v in cycle]
    ax2.bar(xs, cycle, color=colors, edgecolor="white", linewidth=0.5)
    ax2.set_xlabel("k in 2^k mod 9")
    ax2.set_ylabel("Digital root")
    ax2.set_title("Rodin doubling cycle (never hits 3,6,9)")
    ax2.set_ylim(0, 10)
    ax2.axhline(3, color="#e63946", ls="--", alpha=0.3, lw=0.8)
    ax2.axhline(6, color="#e63946", ls="--", alpha=0.3, lw=0.8)
    ax2.axhline(9, color="#e63946", ls="--", alpha=0.3, lw=0.8)

    fig.suptitle(
        f"φ→{mapping['phi']['tens_unit']:.2f}  e→{mapping['e']['tens_unit']:.2f}  "
        f"π→{mapping['pi']['tens_unit']:.2f} (angle/10°)",
        fontsize=11,
    )
    fig.tight_layout()

    out = OUTPUT_DIR / "vortex_369_clock.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    mapping = map_angles_to_369_tens()
    cycle = rodin_doubling_cycle(12)
    clock = clock_positions()
    plot_path = plot_clock_and_rodin(mapping)

    result = {
        "phi_e_pi_369_mapping": mapping,
        "rodin_doubling_cycle_first_12": cycle,
        "clock_positions": clock,
        "interpretation": (
            "3-6-9 as tens-of-degrees markers: exact 30-60-90 maps to 3-6-9; "
            "φ-e-π triangle angles map to ~3.10, ~5.99, ~8.91 — near but not on axis."
        ),
        "plot": str(plot_path),
    }
    report_path = save_report("vortex_369_clock", result)

    print("=== Vortex 3-6-9 / Clock Geometry ===")
    print(f"φ angle / 10° = {mapping['phi']['tens_unit']:.3f}  (nearest 369: {mapping['phi']['nearest_369']})")
    print(f"e angle / 10° = {mapping['e']['tens_unit']:.3f}  (nearest 369: {mapping['e']['nearest_369']})")
    print(f"π angle / 10° = {mapping['pi']['tens_unit']:.3f}  (nearest 369: {mapping['pi']['nearest_369']})")
    print(f"Rodin 2^k mod 9 (k=0..11): {cycle}")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())