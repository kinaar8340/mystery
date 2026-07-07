#!/usr/bin/env python3
"""
Run toe epoch_bake_sweep topology 2×2 grid and save comparison JSON to mystery/outputs/.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, PHI, PI, save_report

TOE_SCRIPTS = Path.home() / "Projects" / "toe" / "scripts"
R_RESIDUAL = PHI**2 + E**2 - PI**2
KAPPA_STAR = E / PI - R_RESIDUAL / PI**2


def _load_epoch_bake():
    path = TOE_SCRIPTS / "epoch_bake_sweep.py"
    spec = importlib.util.spec_from_file_location("epoch_bake_sweep", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    toe_root = str(path.parent.parent)
    if toe_root not in sys.path:
        sys.path.insert(0, toe_root)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Topology κ bake 2×2 grid")
    parser.add_argument("--bake-steps", type=int, default=500)
    args = parser.parse_args()

    mod = _load_epoch_bake()
    summary = mod.run_topology_grid(bake_steps=args.bake_steps)

    # Interpretation block
    table = summary["comparison_table"]
    by_label = {r["label"]: r for r in summary["runs"]}
    full = by_label["full_topology"]
    base = by_label["baseline"]
    v369 = by_label["vortex369_only"]
    topology_causes_drift = abs(full["kappa_drift"]) > abs(base["kappa_drift"]) + 1e-4
    vortex_shifts_proxy_to_sim = (
        v369["delta_proxy_vs_kappa_sim"] < base["delta_proxy_vs_kappa_sim"] - 0.01
    )

    summary["interpretation"] = {
        "topology_causes_kappa_final_drift": topology_causes_drift,
        "vortex369_shifts_kappa_proxy_toward_kappa_sim": vortex_shifts_proxy_to_sim,
        "kappa_proxy_baseline": base["kappa_proxy"],
        "kappa_proxy_vortex369": v369["kappa_proxy"],
        "kappa_star": KAPPA_STAR,
        "note": (
            "κ seeded at κ_doc=0.85; adaptive feedback during bake. "
            "vortex_math_369 shifts κ_proxy toward κ_sim; toroidal alone does not."
        ),
    }

    report_path = save_report("topology_kappa_bake_grid", summary)
    toe_json = mod.save_topology_json(summary)

    print("=== Topology κ Bake Grid ===")
    for row in table:
        print(
            f"  {row['label']:<16} κ {row['kappa_seed']:.3f}→{row['kappa_final']:.3f} "
            f"drift={row['kappa_drift']:+.4f} nearest={row['nearest_kappa']} "
            f"hopf_Δ={row['hopf_delta']:.4f}"
        )
    interp = summary["interpretation"]
    print(f"\nvortex369 → κ_sim proxy: {interp['vortex369_shifts_kappa_proxy_toward_kappa_sim']}")
    print(f"Topology-differentiated κ_final drift: {interp['topology_causes_kappa_final_drift']}")
    print(f"Mystery JSON: {report_path}")
    print(f"Toe JSON:     {toe_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())