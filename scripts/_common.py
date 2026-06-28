"""Shared utilities for Mystery analysis scripts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# High-precision constants (φ from closed form; e and π from numpy long double)
PHI = (1.0 + np.sqrt(5.0)) / 2.0
E = np.e
PI = np.pi


def save_report(name: str, data: dict) -> Path:
    """Write JSON report with UTC timestamp."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{name}_{stamp}.json"
    payload = {"generated_utc": datetime.now(timezone.utc).isoformat(), **data}
    path.write_text(json.dumps(payload, indent=2, default=_json_default))
    return path


def _json_default(obj):
    if isinstance(obj, (np.floating, np.integer)):
        return float(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")


def triangle_angles(a: float, b: float, c: float) -> dict[str, float]:
    """Angles opposite sides a, b, c (law of cosines)."""
    def angle(opposite: float, adj1: float, adj2: float) -> float:
        cos_a = (adj1**2 + adj2**2 - opposite**2) / (2 * adj1 * adj2)
        cos_a = np.clip(cos_a, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_a)))

    return {
        f"opposite_{a:.4g}": angle(a, b, c) if a == min(a, b, c) else None,
        "angle_a_deg": angle(a, b, c),
        "angle_b_deg": angle(b, a, c),
        "angle_c_deg": angle(c, a, b),
    }


def law_of_cosines_angle(opposite: float, side1: float, side2: float) -> float:
    cos_theta = (side1**2 + side2**2 - opposite**2) / (2 * side1 * side2)
    return float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))