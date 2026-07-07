#!/usr/bin/env python3
"""Run the full Mystery analysis suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOE_PYTHON = Path.home() / "Projects" / "toe" / "venv" / "bin" / "python"

SCRIPTS = [
    ("phi_e_pi_analysis.py", None),
    ("hopf_constant_bridge.py", None),
    ("vortex_369_clock.py", None),
    ("brackish_clock.py", None),
    ("residual_bound_probe.py", None),
    ("residual_kappa_sweep.py", None),
    ("skyrme_bound_derivation.py", None),
    ("pde_survival_eigenstructure.py", None),
    ("pde_relaxation_probe.py", None),
    ("exponential_survival_probe.py", TOE_PYTHON),
    ("kappa_survival_sweep.py", None),
    ("golden_angle_twist_probe.py", TOE_PYTHON),
    ("analog_comparative_sweep.py", TOE_PYTHON),
    ("analog_cross_analysis.py", TOE_PYTHON),
    ("pde_structured_ic_probe.py", None),
    ("rodin_hopf_fiber_map.py", None),
    ("conduit_probe.py", TOE_PYTHON),
    ("conduit_angular_probe.py", TOE_PYTHON),
    ("meta_optimize_phi_probe.py", TOE_PYTHON),
]


def python_for(override: Path | None) -> str:
    if override and override.is_file():
        return str(override)
    return sys.executable


def main() -> int:
    print("Mystery — φ, e, π harmonic synthesis\n" + "=" * 50)
    failed = 0
    for name, py_override in SCRIPTS:
        path = ROOT / "scripts" / name
        py = python_for(py_override)
        print(f"\n▶ {name}")
        print("-" * 40)
        rc = subprocess.call([py, str(path)])
        if rc != 0:
            failed += 1
            print(f"  ✗ exit {rc}")
        else:
            print(f"  ✓ done")

    print("\n" + "=" * 50)
    if failed:
        print(f"Finished with {failed} failure(s). See outputs/ for reports.")
        return 1
    print("All scripts completed. Reports in outputs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())