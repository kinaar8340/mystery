#!/usr/bin/env python3
"""
Probe ~/Projects/toe conduit for topological invariants without full Ray/GPU stack.
Gracefully skips if torch or toe dependencies are unavailable.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, PI, TOE_ROOT, load_toe_conduit, save_report


def probe() -> dict:
    module, err = load_toe_conduit()
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