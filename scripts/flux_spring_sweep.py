#!/usr/bin/env python3
"""Parameter sweep for flux_spring — discover reference values via simulation metrics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report
from flux_spring import FLUX_SPRING_CONFIG, brackish_flux, merge_flux_spring_config, nested_orb_physics

R = PHI**2 + E**2 - PI**2
N_ORBS = 5
DURATION = 8.0
N_SAMPLES = 80

# One-at-a-time sweeps (hold other params at FLUX_SPRING_CONFIG defaults).
SWEEP_AXES: dict[str, np.ndarray] = {
    "flux_gauge_rigidness": np.linspace(0.15, 0.95, 9),
    "compression_strength": np.linspace(0.05, 0.40, 8),
    "base_coupling": np.linspace(0.30, 0.95, 8),
    "flux_influence_on_rigidness": np.linspace(0.0, 0.35, 8),
    "inner_emergent_expansion": np.linspace(0.05, 0.60, 8),
    "twist_coupling_blend": np.linspace(0.15, 0.85, 8),
}

BRACKISH_BASE = {
    "base": 1.0,
    "amplitude": 0.4,
    "freq": 0.01,
    "residual_weight": 0.15,
    "stable_mode": False,
}


def _flux_series() -> np.ndarray:
    times = np.linspace(0.0, DURATION, N_SAMPLES)
    return np.array(
        [brackish_flux(float(t), residual_r=R, **BRACKISH_BASE) for t in times],
        dtype=float,
    )


def _trajectory_metrics(flux_values: np.ndarray, **spring_cfg: float) -> dict[str, float]:
    """Aggregate metrics over a flux time series for one config."""
    outer_r: list[float] = []
    inner_r: list[float] = []
    contrasts: list[float] = []
    twists: list[float] = []
    pointers: list[float] = []
    compressions: list[float] = []

    for idx, flux in enumerate(flux_values):
        t = float(idx) * DURATION / max(1, len(flux_values) - 1)
        physics = nested_orb_physics(float(flux), N_ORBS, t=t, **spring_cfg)
        radii = physics.radius_factors
        outer_r.append(radii[-1])
        inner_r.append(radii[0])
        contrasts.append(max(radii) - min(radii))
        twists.append(max(physics.twist_blend))
        pointers.append(physics.global_pointer_deg)
        compressions.append(physics.spring["outer_compression"])

    outer_arr = np.asarray(outer_r)
    inner_arr = np.asarray(inner_r)
    contrast_arr = np.asarray(contrasts)
    twist_arr = np.asarray(twists)
    pointer_arr = np.asarray(pointers)
    comp_arr = np.asarray(compressions)

    # Outer should compress more than inner at high flux (solar-wind rule).
    high_mask = flux_values >= np.quantile(flux_values, 0.75)
    low_mask = flux_values <= np.quantile(flux_values, 0.25)
    compression_gradient = float(
        np.mean(inner_arr[high_mask] - outer_arr[high_mask])
        - np.mean(inner_arr[low_mask] - outer_arr[low_mask])
    )

    return {
        "outer_r_min": float(outer_arr.min()),
        "outer_r_max": float(outer_arr.max()),
        "outer_r_swing": float(outer_arr.max() - outer_arr.min()),
        "inner_r_min": float(inner_arr.min()),
        "inner_r_max": float(inner_arr.max()),
        "inner_r_swing": float(inner_arr.max() - inner_arr.min()),
        "radius_contrast_mean": float(contrast_arr.mean()),
        "radius_contrast_max": float(contrast_arr.max()),
        "twist_blend_mean": float(twist_arr.mean()),
        "twist_blend_max": float(twist_arr.max()),
        "pointer_range_deg": float(np.ptp(pointer_arr)),
        "compression_min": float(comp_arr.min()),
        "compression_swing": float(comp_arr.max() - comp_arr.min()),
        "compression_gradient": compression_gradient,
        "flux_min": float(flux_values.min()),
        "flux_max": float(flux_values.max()),
    }


def _score_metrics(m: dict[str, float]) -> float:
    """
    Higher = more expressive yet stable.

    Rewards visible layer separation + compression gradient; penalizes floor-clamp
    and extreme twist saturation.
    """
    score = 0.0
    score += 2.5 * m["radius_contrast_mean"]
    score += 1.5 * m["outer_r_swing"]
    score += 1.0 * max(0.0, m["compression_gradient"])
    score += 0.8 * m["compression_swing"]
    score += 0.5 * m["twist_blend_mean"]

    if m["compression_min"] <= 0.56:
        score -= 2.0
    if m["twist_blend_max"] > 0.92:
        score -= 1.5
    if m["radius_contrast_mean"] < 0.008:
        score -= 2.0
    if m["pointer_range_deg"] > 120.0:
        score -= 0.5
    return float(score)


def sweep_axis(axis: str, values: np.ndarray, flux_values: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    for val in values:
        cfg = merge_flux_spring_config(**{axis: float(val)})
        metrics = _trajectory_metrics(flux_values, **cfg)
        rows.append(
            {
                "param": axis,
                "value": float(val),
                "score": _score_metrics(metrics),
                **metrics,
            }
        )
    return rows


def recommend_per_axis(rows: list[dict]) -> dict[str, dict]:
    by_param: dict[str, list[dict]] = {}
    for row in rows:
        by_param.setdefault(row["param"], []).append(row)

    recs: dict[str, dict] = {}
    for param, group in by_param.items():
        best = max(group, key=lambda r: r["score"])
        default_val = FLUX_SPRING_CONFIG[param]
        default_row = min(group, key=lambda r: abs(r["value"] - default_val))
        recs[param] = {
            "recommended": best["value"],
            "recommended_score": best["score"],
            "current_default": default_val,
            "current_score": default_row["score"],
            "delta_score": best["score"] - default_row["score"],
        }
    return recs


def grid_rigidness_compression(flux_values: np.ndarray) -> list[dict]:
    """2D sweep on the two most impactful knobs."""
    rigid_vals = np.linspace(0.25, 0.90, 7)
    comp_vals = np.linspace(0.08, 0.35, 7)
    grid: list[dict] = []
    for rigid in rigid_vals:
        for comp in comp_vals:
            cfg = merge_flux_spring_config(
                flux_gauge_rigidness=float(rigid),
                compression_strength=float(comp),
            )
            metrics = _trajectory_metrics(flux_values, **cfg)
            grid.append(
                {
                    "flux_gauge_rigidness": float(rigid),
                    "compression_strength": float(comp),
                    "score": _score_metrics(metrics),
                    **metrics,
                }
            )
    return grid


def build_reference_bundle(
    axis_recs: dict[str, dict],
    grid: list[dict],
) -> dict[str, float]:
    """Compose a single reference config from per-axis winners + grid peak."""
    ref = dict(FLUX_SPRING_CONFIG)
    for param, rec in axis_recs.items():
        if rec["delta_score"] > 0.15:
            ref[param] = rec["recommended"]

    grid_best = max(grid, key=lambda r: r["score"])
    ref["flux_gauge_rigidness"] = grid_best["flux_gauge_rigidness"]
    ref["compression_strength"] = grid_best["compression_strength"]
    return ref


def main() -> int:
    flux_values = _flux_series()
    all_rows: list[dict] = []
    for axis, values in SWEEP_AXES.items():
        all_rows.extend(sweep_axis(axis, values, flux_values))

    axis_recs = recommend_per_axis(all_rows)
    grid = grid_rigidness_compression(flux_values)
    reference = build_reference_bundle(axis_recs, grid)

    ref_metrics = _trajectory_metrics(flux_values, **reference)
    default_metrics = _trajectory_metrics(flux_values, **FLUX_SPRING_CONFIG)

    result = {
        "brackish_driver": BRACKISH_BASE,
        "residual_r": float(R),
        "n_orbs": N_ORBS,
        "duration_s": DURATION,
        "flux_range": [float(flux_values.min()), float(flux_values.max())],
        "current_defaults": dict(FLUX_SPRING_CONFIG),
        "per_axis_recommendations": axis_recs,
        "grid_best": max(grid, key=lambda r: r["score"]),
        "proposed_reference": reference,
        "metrics_default": default_metrics,
        "metrics_proposed": ref_metrics,
        "score_default": _score_metrics(default_metrics),
        "score_proposed": _score_metrics(ref_metrics),
        "sweep_rows": all_rows,
        "grid_rows": grid,
    }

    report_path = save_report("flux_spring_sweep", result)
    json_path = OUTPUT_DIR / "flux_spring_sweep.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("=== flux_spring parameter sweep ===")
    print(f"flux range: {flux_values.min():.3f} … {flux_values.max():.3f}")
    print(f"score (current defaults): {_score_metrics(default_metrics):.3f}")
    print(f"score (proposed reference): {_score_metrics(ref_metrics):.3f}")
    print()
    print("Per-axis recommendations (value | score Δ vs default):")
    for param, rec in axis_recs.items():
        arrow = "↑" if rec["delta_score"] > 0.05 else "≈"
        print(
            f"  {param:32s}  {rec['recommended']:.3f}  "
            f"(default {rec['current_default']:.3f}, Δ{rec['delta_score']:+.2f}) {arrow}"
        )
    print()
    gb = result["grid_best"]
    print(
        f"Grid peak: rigidness={gb['flux_gauge_rigidness']:.2f}, "
        f"compression={gb['compression_strength']:.2f}, score={gb['score']:.3f}"
    )
    print()
    print("Proposed reference config:")
    for k, v in reference.items():
        mark = " *" if abs(v - FLUX_SPRING_CONFIG[k]) > 1e-6 else ""
        print(f"  {k:32s} {v:.3f}{mark}")
    print()
    print(f"Reports: {report_path}")
    print(f"JSON:    {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())