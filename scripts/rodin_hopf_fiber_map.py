#!/usr/bin/env python3
"""
Map Rodin mod-9 doubling cycle onto Hopf S¹ fiber phase increments.
Conceptual bridge: discrete 1-2-4-8-7-5 vs continuous fiber holonomy.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUTPUT_DIR, PI, save_report

KAPPA = 0.85
W_G = 350.0 / PI
RODIN_CYCLE = [1, 2, 4, 8, 7, 5]  # 2^k mod 9, avoids 3-6-9


def digital_root(n: int) -> int:
    if n == 0:
        return 9
    r = n % 9
    return 9 if r == 0 else r


def rodin_doubling_steps(n_steps: int = 12) -> list[int]:
    return [digital_root(2**k) for k in range(n_steps)]


def fiber_phase_increments(digits: list[int], mode: str = "tens_degrees") -> list[float]:
    """
    Map digit d to fiber phase increment:
    - tens_degrees: Δθ = d × 10° (clock / 3-6-9 positional)
    - ninth_turn:   Δθ = d × (2π/9) rad (uniform partition of S¹)
    - hopf_weighted: Δθ = d × (2π/W_g) / 9 (scaled by locked winding)
    """
    out = []
    for d in digits:
        if mode == "tens_degrees":
            out.append(d * 10.0)
        elif mode == "ninth_turn":
            out.append(d * (2 * PI / 9))
        elif mode == "hopf_weighted":
            out.append(d * (2 * PI / W_G) / 9)
        else:
            raise ValueError(mode)
    return out


def cumulative_phase(digits: list[int], mode: str) -> np.ndarray:
    inc = fiber_phase_increments(digits, mode)
    return np.cumsum(inc)


def axis_369_markers() -> dict:
    return {
        "3": {"tens_deg": 30, "ninth_turn_rad": 2 * PI / 3, "role": "control axis"},
        "6": {"tens_deg": 60, "ninth_turn_rad": 4 * PI / 3, "role": "control axis"},
        "9": {"tens_deg": 90, "ninth_turn_rad": 2 * PI, "role": "control axis / full turn"},
    }


def holonomy_damping_per_step(kappa: float = KAPPA, dt: float = 1.0) -> float:
    """Observer sync: δΘ(t) = δΘ(0) exp(−κt) per unit step."""
    return float(np.exp(-kappa * dt))


def plot_map(path: Path) -> None:
    digits = rodin_doubling_steps(12)
    modes = ["tens_degrees", "ninth_turn", "hopf_weighted"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    ax = axes[0, 0]
    xs = np.arange(len(digits))
    colors = ["#e63946" if d in (3, 6, 9) else "#1d3557" for d in digits]
    ax.bar(xs, digits, color=colors)
    ax.set_title("Rodin 2^k mod 9")
    ax.set_ylabel("Digital root")
    ax.set_xlabel("k")

    for ax, mode in zip([axes[0, 1], axes[1, 0], axes[1, 1]], modes):
        cum = cumulative_phase(digits, mode)
        ax.plot(cum, "o-", color="#c9a227", lw=1.5)
        for t in (30, 60, 90) if mode == "tens_degrees" else []:
            ax.axhline(t, color="#e63946", ls="--", alpha=0.4, lw=0.8)
        ax.set_title(f"Cumulative fiber phase ({mode})")
        ax.set_xlabel("doubling step k")
        ax.grid(alpha=0.3)

    fig.suptitle("Rodin doubling → Hopf S¹ fiber phase (conceptual map)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    digits = rodin_doubling_steps(24)
    mappings = {}
    for mode in ("tens_degrees", "ninth_turn", "hopf_weighted"):
        inc = fiber_phase_increments(digits[:12], mode)
        cum = cumulative_phase(digits[:12], mode)
        mappings[mode] = {
            "increments_first_12": inc,
            "cumulative_end": float(cum[-1]),
            "mean_increment": float(np.mean(inc)),
        }

    payload = {
        "rodin_cycle_period_6": RODIN_CYCLE,
        "doubling_first_12": digits[:12],
        "axis_369_markers": axis_369_markers(),
        "fiber_phase_mappings": mappings,
        "holonomy_damping_per_unit_step": holonomy_damping_per_step(),
        "W_g": float(W_G),
        "kappa": KAPPA,
        "interpretation": (
            "Rodin cycle never hits 3-6-9; those digits mark orthogonal control axes at "
            "30°/60°/90° (tens_degrees map). Doubling orbit accumulates fiber phase; "
            "hopf_weighted map scales increments by W_g⁻¹. Full derivation requires "
            "matching discrete mod-9 to continuum quaternion holonomy α = −κΘ̄."
        ),
        "open_work": "Prove or falsify: does two-gyro drive align doubling steps with "
        "quantized ΔΘ increments at burst-reset events?",
    }
    plot_path = OUTPUT_DIR / "rodin_hopf_fiber_map.png"
    plot_map(plot_path)
    payload["plot"] = str(plot_path)

    report_path = save_report("rodin_hopf_fiber_map", payload)
    print("=== Rodin ↔ Hopf Fiber Map ===")
    print(f"Cycle: {RODIN_CYCLE}")
    print(f"Cumulative (tens_deg, 12 steps): {mappings['tens_degrees']['cumulative_end']:.1f}°")
    print(f"Cumulative (ninth_turn rad): {mappings['ninth_turn']['cumulative_end']:.4f}")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())