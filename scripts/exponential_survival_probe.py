#!/usr/bin/env python3
"""
exponential_survival_probe.py
=============================
Run PDE + conduit dynamics normalized to λt = 2 and compare survival
fractions / residuals to e^{−2}, R = φ²+e²−π², and golden-angle analogs.

Mapping: mean-field gauge −κθ̄ ⇒ λ ≈ κ; at λt = 2 the universal memoryless
survival fraction is exp(−2) ≈ 0.135335.

PDE / survival: flux_hopf_lib.simulation
Conduit (optional): toe RubikConeConduit
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    E_INV2,
    GOLDEN_ANGLE_FRACTION,
    PHI,
    PI,
    R_RESIDUAL,
    load_toe_conduit,
    save_report,
    simulate_twist_pde_survival,
)


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
    try:
        pde_result = simulate_twist_pde_survival(
            normalize_to_lambda_t=2.0,
            kappa=0.85,
            dt=0.001,
            seed=42,
        )
        pde_result["status"] = "ok"
        pde_result["source"] = "flux_hopf_lib.simulation"
    except Exception as exc:  # noqa: BLE001
        print(f"PDE survival skipped: {exc}")
        pde_result = {"status": "skipped", "reason": str(exc)}

    conduit_result: dict
    conduit_mod, c_err = load_toe_conduit()
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
        "source": "flux_hopf_lib",
    }

    table_rows: list[dict] = []
    if pde_result.get("status") == "ok":
        for _key, comp in pde_result["analog_comparisons"].items():
            table_rows.append(comp)

    if conduit_result.get("status") == "ok":
        for _key, comp in conduit_result.get("analog_comparisons", {}).items():
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
    print(
        f"References: R={R_RESIDUAL:.6f}  e^{{-2}}={E_INV2:.6f}  "
        f"golden/1000={GOLDEN_ANGLE_FRACTION:.6f}"
    )
    print()

    if pde_result.get("status") == "ok":
        norm = pde_result["normalization"]
        surv = pde_result["survival"]
        print(
            f"PDE: n_steps={norm['n_steps']}  t_phys={norm['t_physical']:.4f}  "
            f"κ={norm['kappa']}  [flux_hopf_lib]"
        )
        print(
            f"     mean_survival={surv['mean_survival']:.6f}  "
            f"std_survival={surv['std_survival']:.6f}  "
            f"fluct_survival={surv['fluctuation_survival']:.6f}"
        )
        best = pde_result["analog_comparisons"]["mean_survival"]
        print(
            f"     mean_survival best match: {best['best_match']} "
            f"(Δ {best['delta_pct_vs_best']:.2f}%)"
        )
        if "hybrid_score" in best:
            print(
                f"     hybrid score: {best['hybrid_score']:.4f}  "
                f"(Δ% {best.get('hybrid_delta_pct', 0):.2f})"
            )

    if conduit_result.get("status") == "ok":
        gt = conduit_result["gauged_twist"]
        print(f"Conduit: n_steps={gt['n_steps']}  λt={gt['lambda_t_achieved']:.4f}")
        print(
            f"         identity_survival={gt['identity_survival']:.6f}  "
            f"identity_residual={gt['identity_residual']:.6f}  "
            f"twist_survival={gt.get('twist_survival', 0):.6f}"
        )
        print(
            f"         braiding_residual={conduit_result['braiding_residual']:.6f}  "
            f"W_g rel.residual={conduit_result['wg_relative_residual']:.6f}"
        )
    elif conduit_result.get("status") == "skipped":
        print(f"Conduit skipped: {conduit_result.get('reason')}")

    if table_rows:
        print()
        print(format_comparison_table(table_rows))

    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
