#!/usr/bin/env python3
"""
exponential_survival_probe.py
=============================
Run PDE + conduit dynamics normalized to λt = 2 and compare survival
fractions / residuals to e^{−2}, R = φ²+e²−π², and golden-angle analogs.

Mapping: mean-field gauge −κθ̄ ⇒ λ ≈ κ; at λt = 2 the universal memoryless
survival fraction is exp(−2) ≈ 0.135335.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

TOE_ROOT = Path.home() / "Projects" / "toe"
TOE_SRC = TOE_ROOT / "src"

R_RESIDUAL = PHI**2 + E**2 - PI**2
E_INV2 = float(np.exp(-2.0))
GOLDEN_ANGLE_FRACTION = 360.0 * (1.0 - 1.0 / PHI) / 1000.0


def _import_relaxation_survival():
    path = TOE_SRC / "relaxation_survival.py"
    if not path.is_file():
        return None, f"Missing {path}"
    for p in (str(TOE_SRC), str(TOE_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("relaxation_survival", path)
    if spec is None or spec.loader is None:
        return None, "Could not load relaxation_survival spec"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return mod, None


def _import_conduit():
    path = TOE_SRC / "conduit.py"
    if not path.is_file():
        return None, f"Missing {path}"
    try:
        import torch  # noqa: F401
    except ImportError:
        return None, "torch not installed"
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


def format_comparison_table(rows: list[dict]) -> str:
    lines = [
        f"{'Metric':<28} {'Measured':>10} {'Best analog':>14} {'Δ%':>8}",
        "-" * 64,
    ]
    for row in rows:
        lines.append(
            f"{row['label']:<28} {row['measured']:>10.6f} {row['best_match']:>14} "
            f"{row['delta_pct_vs_best']:>7.2f}%"
        )
    return "\n".join(lines)


def main() -> int:
    rs_mod, rs_err = _import_relaxation_survival()
    if rs_mod is None:
        print(f"PDE survival skipped: {rs_err}")
        pde_result = {"status": "skipped", "reason": rs_err}
    else:
        pde_result = rs_mod.simulate_twist_pde_survival(
            normalize_to_lambda_t=2.0,
            kappa=0.85,
            dt=0.001,
            seed=42,
        )
        pde_result["status"] = "ok"

    conduit_result: dict
    conduit_mod, c_err = _import_conduit()
    if conduit_mod is None:
        conduit_result = {"status": "skipped", "reason": c_err}
    else:
        import torch

        RubikConeConduit = conduit_mod.RubikConeConduit
        device = "cuda" if torch.cuda.is_available() else "cpu"
        conduit = RubikConeConduit(
            wg_base=350.0,
            kappa=0.85,
            braiding_target=0.8145,
            toroidal_modulo9=True,
            vortex_math_369=True,
        ).to(device)
        conduit_result = conduit.run_survival_probe(
            normalize_to_lambda_t=2.0, dt=0.001, seed=42
        )
        conduit_result["status"] = "ok"
        conduit_result["device"] = device

    reference = {
        "R_phi_e_pi": R_RESIDUAL,
        "e_inv2": E_INV2,
        "golden_angle_over_1000": GOLDEN_ANGLE_FRACTION,
        "kappa_doc": 0.85,
        "W_g_target": 350.0 / PI,
        "braiding_target": 0.8145,
    }

    table_rows: list[dict] = []
    if pde_result.get("status") == "ok":
        for key, comp in pde_result["analog_comparisons"].items():
            table_rows.append(comp)

    if conduit_result.get("status") == "ok":
        for key, comp in conduit_result["analog_comparisons"].items():
            table_rows.append(comp)

    result = {
        "reference_analogs": reference,
        "pde_survival": pde_result,
        "conduit_survival": conduit_result,
        "comparison_table": table_rows,
        "interpretation": (
            "At λt=2 (λ≈κ), mean-field survival should track e^{−2}≈0.1353. "
            "Deviations quantify dissipative corrections; proximity to R≈0.1375 "
            "or golden-angle fraction is an emergent signature, not an identity."
        ),
    }

    report_path = save_report("exponential_survival_probe", result)

    print("=== Exponential Survival Probe (λt = 2) ===")
    print(f"References: R={R_RESIDUAL:.6f}  e^{{-2}}={E_INV2:.6f}  "
          f"golden/1000={GOLDEN_ANGLE_FRACTION:.6f}")
    print()

    if pde_result.get("status") == "ok":
        norm = pde_result["normalization"]
        surv = pde_result["survival"]
        print(f"PDE: n_steps={norm['n_steps']}  t_phys={norm['t_physical']:.4f}  κ={norm['kappa']}")
        print(f"     mean_survival={surv['mean_survival']:.6f}  "
              f"std_survival={surv['std_survival']:.6f}  "
              f"fluct_survival={surv['fluctuation_survival']:.6f}")
        best = pde_result["analog_comparisons"]["mean_survival"]
        print(f"     mean_survival best match: {best['best_match']} "
              f"(Δ {best['delta_pct_vs_best']:.2f}%)")
        if "hybrid_score" in best:
            print(f"     hybrid score: {best['hybrid_score']:.4f}  "
                  f"(Δ% {best.get('hybrid_delta_pct', 0):.2f})")

    if conduit_result.get("status") == "ok":
        gt = conduit_result["gauged_twist"]
        print(f"Conduit: n_steps={gt['n_steps']}  λt={gt['lambda_t_achieved']:.4f}")
        print(f"         identity_survival={gt['identity_survival']:.6f}  "
              f"identity_residual={gt['identity_residual']:.6f}  "
              f"twist_survival={gt.get('twist_survival', 0):.6f}")
        print(f"         braiding_residual={conduit_result['braiding_residual']:.6f}  "
              f"W_g rel.residual={conduit_result['wg_relative_residual']:.6f}")

    if table_rows:
        print()
        print(format_comparison_table(table_rows))

    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())