#!/usr/bin/env python3
"""
Run toe meta_optimize_invariants (lightweight) and test φ/e/π clustering in emergent constants.
Writes report to ~/Projects/mystery/outputs/.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MYSTERY_ROOT = Path(__file__).resolve().parent.parent
TOE_ROOT = Path.home() / "Projects" / "toe"
OUTPUT_DIR = MYSTERY_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHI = (1 + np.sqrt(5)) / 2
E = np.e
PI = np.pi


def phi_e_pi_targets() -> dict:
    return {
        "phi": PHI,
        "e": E,
        "pi": PI,
        "e_over_pi": E / PI,
        "phi_over_e": PHI / E,
        "phi_over_pi": PHI / PI,
        "pi_times_1_plus_kappa_at_085": PI * (1 + 0.85),
    }


def nearest_label(value: float, targets: dict[str, float]) -> tuple[str, float]:
    best = min(targets.items(), key=lambda kv: abs(value - kv[1]))
    return best[0], 100 * abs(value - best[1]) / abs(best[1])


def run_meta_optimize(trials: int = 20) -> dict:
    """Invoke toe meta_optimize_invariants.py and parse stdout."""
    script = TOE_ROOT / "scripts" / "meta_optimize_invariants.py"
    python = TOE_ROOT / "venv" / "bin" / "python"
    if not python.is_file():
        python = Path(sys.executable)

    if not script.is_file():
        return {"status": "error", "reason": f"Missing {script}"}

    try:
        proc = subprocess.run(
            [str(python), str(script), "--trials", str(trials)],
            cwd=str(TOE_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "trials": trials}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": str(exc)}

    stdout = proc.stdout + proc.stderr
    result = {
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "trials": trials,
        "stdout_tail": stdout[-4000:],
    }

    for line in stdout.splitlines():
        if "Emergent wg_base:" in line:
            try:
                part = line.split("Wg =")[1].strip()
                result["best_w_g"] = float(part)
            except (IndexError, ValueError):
                pass
        if "Emergent κ:" in line:
            try:
                result["best_kappa"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        if "Emergent braiding_target:" in line:
            try:
                result["best_braiding"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        if "Best loss:" in line:
            try:
                result["best_loss"] = float(line.split(":")[-1].strip())
            except ValueError:
                pass

    return result


def analyze_clustering(meta: dict) -> dict:
    targets = phi_e_pi_targets()
    analysis = {"targets": targets, "clustering": {}}

    if meta.get("best_kappa") is not None:
        k = meta["best_kappa"]
        label, delta = nearest_label(k, {"e_over_pi": E / PI, "phi_inv": 1 / PHI, "kappa_doc": 0.85})
        analysis["clustering"]["kappa"] = {
            "value": k,
            "nearest": label,
            "delta_pct": delta,
            "theta_crit_pi_1_plus_kappa": PI * (1 + k),
        }

    if meta.get("best_braiding") is not None:
        b = meta["best_braiding"]
        label, delta = nearest_label(
            b, {"phi_b_doc": 0.8145, "phi_inv": 1 / PHI, "phi_over_pi": PHI / PI}
        )
        analysis["clustering"]["braiding"] = {"value": b, "nearest": label, "delta_pct": delta}

    if meta.get("best_w_g") is not None:
        w = meta["best_w_g"]
        target_w = 350 / PI
        analysis["clustering"]["w_g"] = {
            "value": w,
            "target_350_over_pi": target_w,
            "delta_pct": 100 * abs(w - target_w) / target_w,
        }

    return analysis


def main() -> int:
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    print(f"Running meta_optimize_invariants ({trials} trials)...")
    meta = run_meta_optimize(trials)
    analysis = analyze_clustering(meta)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "meta_optimize": meta,
        "phi_e_pi_clustering": analysis,
        "theta_crit_reconciliation": {
            "theta_link_rad": 2 * PI * (350 / PI) / (2 * (350 / PI) + 1),
            "theta_crit_formula_rad": PI * (1 + meta.get("best_kappa", 0.85)),
            "theta_crit_sim_default": 5.8,
        },
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"meta_optimize_phi_probe_{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, default=float))
    print(f"Report: {path}")

    if meta.get("status") == "ok":
        print(f"Best κ={meta.get('best_kappa')} → nearest {analysis['clustering'].get('kappa', {}).get('nearest')}")
        print(f"Best φ_b={meta.get('best_braiding')}")
        print(f"Best W_g={meta.get('best_w_g')}")
    else:
        print(f"Meta-optimize status: {meta.get('status')} — see report")
    return 0 if meta.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())