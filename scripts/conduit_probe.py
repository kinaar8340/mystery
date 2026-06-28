#!/usr/bin/env python3
"""
Probe ~/Projects/toe conduit for topological invariants without full Ray/GPU stack.
Gracefully skips if torch or toe dependencies are unavailable.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, PI, save_report

TOE_ROOT = Path.home() / "Projects" / "toe"


def try_import_conduit():
    """Import RubikConeConduit from local toe checkout."""
    conduit_path = TOE_ROOT / "src" / "conduit.py"
    if not conduit_path.is_file():
        return None, f"Missing {conduit_path}"

    toe_src = str(TOE_ROOT / "src")
    toe_root = str(TOE_ROOT)
    for p in (toe_src, toe_root):
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        import torch  # noqa: F401
    except ImportError:
        return None, "torch not installed — skipping conduit probe"

    spec = importlib.util.spec_from_file_location("toe_conduit", conduit_path)
    if spec is None or spec.loader is None:
        return None, "Could not load conduit module spec"

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001
        return None, f"conduit import failed: {exc}"

    return module, None


def probe() -> dict:
    module, err = try_import_conduit()
    if module is None:
        return {
            "status": "skipped",
            "reason": err,
            "toe_root": str(TOE_ROOT),
            "hint": "cd ~/Projects/toe && pip install -r requirements.txt",
        }

    import torch

    RubikConeConduit = module.RubikConeConduit
    device = "cuda" if torch.cuda.is_available() else "cpu"

    conduit = RubikConeConduit(
        wg_base=350.0,
        kappa=0.85,
        braiding_target=0.8145,
        toroidal_modulo9=True,
        vortex_math_369=True,
    ).to(device)

    stats = conduit.monitor_topological_winding(n_samples=128)

    geo_w = float(stats.get("geometric_winding", 0.0))
    braiding = float(stats.get("braiding_phase", 0.0))
    w_g_target = 350.0 / PI

    return {
        "status": "ok",
        "device": device,
        "toe_root": str(TOE_ROOT),
        "kappa_input": 0.85,
        "e_over_pi": E / PI,
        "w_g_target": w_g_target,
        "geometric_winding": geo_w,
        "w_g_delta": abs(geo_w - w_g_target),
        "braiding_phase": braiding,
        "braiding_target": 0.8145,
        "vortex_math_369": True,
        "toroidal_modulo9": True,
        "raw_stats": {k: float(v) if hasattr(v, "__float__") else str(v) for k, v in stats.items()},
    }


def main() -> int:
    result = probe()
    report_path = save_report("conduit_probe", result)

    print("=== TOE Conduit Probe ===")
    if result["status"] == "skipped":
        print(f"Skipped: {result['reason']}")
    else:
        print(f"Device: {result['device']}")
        print(f"W_g (geometric) = {result['geometric_winding']:.6f}  (target {result['w_g_target']:.6f})")
        print(f"Braiding phase  = {result['braiding_phase']:.6f}  (target {result['braiding_target']:.4f})")
        print(f"κ = {result['kappa_input']}  |  e/π = {result['e_over_pi']:.6f}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())