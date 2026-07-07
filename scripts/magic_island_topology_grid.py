#!/usr/bin/env python3
"""Run magic_island_sweep island topology grid and save JSON to mystery/outputs/."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import save_report

TOE_SCRIPTS = Path.home() / "Projects" / "toe" / "scripts"


def _load_magic_island():
    path = TOE_SCRIPTS / "magic_island_sweep.py"
    spec = importlib.util.spec_from_file_location("magic_island_sweep", path)
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

    parser = argparse.ArgumentParser(description="Magic island topology κ grid")
    parser.add_argument("--island-z", type=int, default=129, choices=[18, 54, 129])
    parser.add_argument("--quick", action="store_true", default=True)
    parser.add_argument("--braid-gains", type=float, nargs="+", default=[0.002, 0.005, 0.01])
    args = parser.parse_args()

    import os

    toe_root = TOE_SCRIPTS.parent
    os.chdir(toe_root)
    mod = _load_magic_island()
    summary = mod.run_island_topology_grid(
        island_z=args.island_z,
        quick=args.quick,
        braid_gains=args.braid_gains,
    )
    toe_path = mod.save_island_grid_json(summary)
    report_path = save_report(f"magic_island_topology_grid_z{args.island_z}", summary)

    print("=== Magic Island Topology Grid ===")
    for row in summary["comparison_table"]:
        print(
            f"  {row['label']:<28} κ→{row['kappa_final']:.3f} "
            f"drift={row['kappa_drift']:+.4f} proxy={row['kappa_proxy']:.3f}"
        )
    print(f"Mystery JSON: {report_path}")
    print(f"Toe JSON:     {toe_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())