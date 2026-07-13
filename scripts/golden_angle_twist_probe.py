#!/usr/bin/env python3
"""
golden_angle_twist_probe.py
===========================
Compare conduit helix geometry with and without golden-angle rotation steps.

Includes S¹ unit-circle phase histogram (better diagnostic than pairwise 3D chords).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    E,
    GOLDEN_ANGLE_DEG,
    OUTPUT_DIR,
    PHI,
    PI,
    R_RESIDUAL,
    load_toe_conduit,
    save_report,
)

GOLDEN_ANGLE_RAD = float(np.radians(GOLDEN_ANGLE_DEG))


def _import_conduit():
    return load_toe_conduit()


def pairwise_angles(positions: np.ndarray) -> np.ndarray:
    norms = positions / (np.linalg.norm(positions, axis=1, keepdims=True) + 1e-8)
    dots = np.sum(norms[:-1] * norms[1:], axis=1)
    dots = np.clip(dots, -1.0, 1.0)
    return np.degrees(np.arccos(dots))


def unit_circle_phases(conduit, n_samples: int = 256) -> np.ndarray:
    """S¹ phases from helix XY projection."""
    s_vals = np.linspace(0.05, conduit.max_depth, n_samples)
    phases = []
    for s in s_vals:
        pos = conduit.get_helix_3d(float(s), 0).detach().cpu().numpy()
        phases.append(float(np.arctan2(pos[1], pos[0]) % (2 * PI)))
    return np.array(phases)


def phase_histogram_stats(phases: np.ndarray, n_bins: int = 36) -> dict:
    """Binned S¹ coverage and proximity to golden-angle increments."""
    hist, edges = np.histogram(phases, bins=n_bins, range=(0, 2 * PI))
    occupied = int(np.sum(hist > 0))
    coverage = occupied / n_bins

    # Phase increments between samples
    deltas = np.diff(np.sort(phases))
    deltas_deg = np.degrees(deltas % (2 * PI))
    near_golden = float(np.mean(np.abs(deltas_deg - GOLDEN_ANGLE_DEG) < 5.0) * 100)

    return {
        "n_bins": n_bins,
        "occupied_bins": occupied,
        "packing_coverage": float(coverage),
        "mean_phase_rad": float(np.mean(phases)),
        "std_phase_rad": float(np.std(phases)),
        "pct_increments_near_golden_5deg": near_golden,
        "hist_counts": hist.tolist(),
        "hist_edges": edges.tolist(),
    }


def plot_phase_histogram(
    phases: np.ndarray,
    label: str,
    out_path: Path,
    *,
    n_bins: int = 36,
) -> None:
    """Polar + Cartesian S¹ phase histogram."""
    fig = plt.figure(figsize=(10, 4))
    ax0 = fig.add_subplot(121)
    ax0.hist(phases, bins=n_bins, range=(0, 2 * PI), color="#c9a227", alpha=0.85, edgecolor="#333")
    for k in range(8):
        tick = (k * GOLDEN_ANGLE_RAD) % (2 * PI)
        ax0.axvline(tick, color="#e76f51", ls="--", lw=0.9, alpha=0.7)
    ax0.set_xlabel("Phase on S¹ (rad)")
    ax0.set_ylabel("Count")
    ax0.set_title(f"S¹ histogram — {label}")
    ax0.grid(alpha=0.3)

    ax1 = fig.add_subplot(122, projection="polar")
    theta_bins = np.linspace(0, 2 * PI, n_bins + 1)
    counts, _ = np.histogram(phases, bins=theta_bins)
    centres = (theta_bins[:-1] + theta_bins[1:]) / 2
    ax1.bar(
        centres, counts, width=2 * PI / n_bins,
        color="#2a9d8f", alpha=0.8, edgecolor="#111",
    )
    ax1.set_title(f"Polar S¹ — {label}", pad=12)

    fig.suptitle(f"Unit-circle projection · golden ref = {GOLDEN_ANGLE_DEG:.2f}°", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def probe_conduit(golden_angle_steps: bool, n_samples: int = 256) -> dict:
    mod, err = _import_conduit()
    if mod is None:
        return {"status": "skipped", "reason": err}

    import torch

    RubikConeConduit = mod.RubikConeConduit
    device = "cuda" if torch.cuda.is_available() else "cpu"
    conduit = RubikConeConduit(
        wg_base=350.0,
        kappa=0.85,
        braiding_target=0.8145,
        toroidal_modulo9=True,
        vortex_math_369=True,
        golden_angle_steps=golden_angle_steps,
    ).to(device)

    s_vals = np.linspace(0.05, conduit.max_depth, n_samples)
    positions = np.array([
        conduit.get_helix_3d(float(s), 0).detach().cpu().numpy() for s in s_vals
    ])
    angles = pairwise_angles(positions)
    phases = unit_circle_phases(conduit, n_samples)
    phase_stats = phase_histogram_stats(phases)
    stats = conduit.monitor_topological_winding(n_samples=n_samples)

    tag = "golden" if golden_angle_steps else "baseline"
    plot_path = OUTPUT_DIR / f"golden_phase_hist_{tag}.png"
    plot_phase_histogram(phases, tag, plot_path)

    return {
        "status": "ok",
        "golden_angle_steps": golden_angle_steps,
        "golden_angle_deg": GOLDEN_ANGLE_DEG,
        "mean_pairwise_angle": float(np.mean(angles)),
        "std_pairwise_angle": float(np.std(angles)),
        "pct_within_5deg_golden_pairwise": float(
            np.mean(np.abs(angles - GOLDEN_ANGLE_DEG) < 5.0) * 100
        ),
        "unit_circle": phase_stats,
        "phase_histogram_plot": str(plot_path),
        "braiding_phase": float(stats.get("braiding_phase", 0.0)),
        "geometric_winding": float(stats.get("geometric_winding", 0.0)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden-angle twist probe")
    parser.add_argument("--golden-angle-steps", action="store_true")
    parser.add_argument("--compare", action="store_true", default=True)
    parser.add_argument("--no-compare", action="store_false", dest="compare")
    args = parser.parse_args()

    if args.compare:
        baseline = probe_conduit(golden_angle_steps=False)
        golden = probe_conduit(golden_angle_steps=True)
        result = {"baseline": baseline, "golden_angle": golden}
    else:
        result = {"run": probe_conduit(golden_angle_steps=args.golden_angle_steps)}

    report_path = save_report("golden_angle_twist_probe", result)

    print("=== Golden-Angle Twist Probe (S¹ phase) ===")
    if "baseline" in result and result["baseline"].get("status") == "ok":
        b, g = result["baseline"], result["golden_angle"]
        print(f"Golden angle reference: {GOLDEN_ANGLE_DEG:.4f}°  R={R_RESIDUAL:.6f}")
        print(f"Baseline  — packing coverage: {b['unit_circle']['packing_coverage']:.3f}  "
              f"Δphase near golden: {b['unit_circle']['pct_increments_near_golden_5deg']:.1f}%")
        print(f"Golden    — packing coverage: {g['unit_circle']['packing_coverage']:.3f}  "
              f"Δphase near golden: {g['unit_circle']['pct_increments_near_golden_5deg']:.1f}%")
        print(f"Plots: {b.get('phase_histogram_plot')}  {g.get('phase_histogram_plot')}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())