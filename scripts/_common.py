"""Shared utilities for Mystery analysis scripts.

Constants and survival/relaxation APIs come from flux_hopf_lib (single source
of truth). TOE conduit loading remains optional via ``load_toe_conduit``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOE_ROOT = Path.home() / "Projects" / "toe"
TOE_SRC = TOE_ROOT / "src"
FLUX_HOPF_LIB_ROOT = Path.home() / "Projects" / "flux_hopf_lib"

# ---------------------------------------------------------------------------
# Canonical constants + survival API (flux_hopf_lib)
# ---------------------------------------------------------------------------
from flux_hopf_lib import (  # noqa: E402
    DEFAULT_KAPPA,
    E,
    E_INV2,
    GOLDEN_ANGLE_DEG,
    GOLDEN_ANGLE_FRACTION,
    PHI,
    PHI_INV2,
    PI,
    R_RESIDUAL,
    W_G_LOCK,
)
from flux_hopf_lib.simulation import (  # noqa: E402
    LambdaTNormalization,
    SurvivalAnalogs,
    compare_to_analogs,
    evolve_gauged_twist_survival,
    simulate_twist_pde_survival,
    steps_for_lambda_t,
)

# Back-compat aliases used by older scripts
R = R_RESIDUAL


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


# ---------------------------------------------------------------------------
# Optional TOE conduit (still lives in toe; not part of flux_hopf_lib yet)
# ---------------------------------------------------------------------------
def load_toe_conduit() -> tuple[Any | None, str | None]:
    """
    Load toe ``conduit`` module (RubikConeConduit).

    Returns (module, error_message). Survival/PDE no longer need this.
    """
    path = TOE_SRC / "conduit.py"
    if not path.is_file():
        return None, f"Missing {path}"
    try:
        import torch  # noqa: F401
    except ImportError:
        return None, "torch not installed (needed for RubikConeConduit)"

    for p in (str(TOE_SRC), str(TOE_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)

    spec = importlib.util.spec_from_file_location("toe_conduit", path)
    if spec is None or spec.loader is None:
        return None, "Could not load conduit spec"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return mod, None
