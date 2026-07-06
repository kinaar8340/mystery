#!/usr/bin/env python3
"""Sweep survival-penalty weight w_s for Stage 6 analog objective tuning."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MYSTERY_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = MYSTERY_ROOT / "outputs"
SCRIPT = MYSTERY_ROOT / "scripts" / "meta_optimize_phi_probe.py"
PYTHON = Path.home() / "Projects" / "toe" / "venv" / "bin" / "python"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sweep w_s for meta_optimize_phi_probe")
    p.add_argument("--weights", type=float, nargs="+", default=[8.0, 10.0, 12.0])
    p.add_argument("--trials", type=int, default=25)
    p.add_argument("--golden-reward-weight", type=float, default=0.3)
    return p.parse_args()


def run_one(w_s: float, trials: int, golden_w: float) -> dict:
    cmd = [
        str(PYTHON),
        str(SCRIPT),
        "--compare-baseline",
        "--trials",
        str(trials),
        "--use-survival-penalty",
        "--golden-angle-steps",
        "--golden-reward-weight",
        str(golden_w),
        "--use-hybrid-objective",
        "--survival-penalty-weight",
        str(w_s),
    ]
    print(f"\n{'=' * 72}\n  w_s = {w_s}  |  trials = {trials}\n{'=' * 72}")
    proc = subprocess.run(cmd, cwd=str(MYSTERY_ROOT), capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0:
        return {"w_s": w_s, "status": "error", "returncode": proc.returncode}
    outputs = sorted(OUTPUT_DIR.glob("meta_optimize_phi_probe_*.json"))
    latest = outputs[-1] if outputs else None
    summary = {"w_s": w_s, "status": "ok", "json": latest.name if latest else None}
    if latest:
        data = json.loads(latest.read_text())
        for row in data.get("comparison_table", []):
            if row.get("mode") == "dual_analog":
                summary["dual_analog"] = row
            if row.get("mode") == "survival_penalty":
                summary["survival_penalty"] = row
            if row.get("mode") == "baseline":
                summary["baseline"] = row
    return summary


def main() -> int:
    args = parse_args()
    results = [run_one(w, args.trials, args.golden_reward_weight) for w in args.weights]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / f"w_s_sweep_{stamp}.json"
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "weights": args.weights,
        "trials_per_mode": args.trials,
        "results": results,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nSweep summary written: {out}")
    print("\n| w_s | dual loss | κ | mean_survival | Δ% vs R | hybrid |")
    print("|-----|-----------|---|---------------|---------|--------|")
    for r in results:
        d = r.get("dual_analog") or {}
        ms = d.get("mean_survival")
        ms_s = f"{ms:.6f}" if ms is not None else "—"
        d_r = d.get("delta_pct_vs_R")
        d_r_s = f"{d_r:.3f}%" if d_r is not None else "—"
        hybrid = d.get("hybrid_score")
        h_s = f"{hybrid:.4f}" if hybrid is not None else "—"
        print(
            f"| {r['w_s']} | {d.get('final_loss', '—')} | {d.get('kappa', '—')} | "
            f"{ms_s} | {d_r_s} | {h_s} |"
        )
    return 0 if all(r.get("status") == "ok" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())