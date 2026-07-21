#!/usr/bin/env python3
"""
Multi-attractor triple-point scan — coexistence of solid/liquid/vapor analogs.

=============================================================================
  NOT H₂O thermodynamics. Asks whether, at a single (κ, Δω) control point,
  different seeds (IC class + RNG seed) land in different phase labels —
  a multi-attractor / triple-point-like coexistence signature.
=============================================================================

Method
  1. Reuse water_phase_analog_sweep dual probes + label_phase().
  2. At each (κ, Δω) on a small grid near the solid/liquid edge and vapor band,
     run an ensemble over IC ∈ {helical, hopfion, tetrahedral, uniform}
     and several RNG seeds.
  3. Count distinct phases among the ensemble.
  4. Flag points with n_phases ≥ 2 (bistable) or ≥ 3 (triple-like coexistence).

Outputs
  outputs/triple_point_scan.png
  outputs/triple_point_scan_<timestamp>.json

Examples
  python scripts/triple_point_scan.py
  python scripts/triple_point_scan.py --quick
  python scripts/triple_point_scan.py --n-kappa 5 --n-domega 5 --n-seeds 4
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PI, save_report  # noqa: E402
from water_phase_analog_sweep import (  # noqa: E402
    IC_CHOICES,
    INT_TO_PHASE,
    LABEL_THRESHOLDS,
    PHASE_COLORS,
    PHASE_LIQUID,
    PHASE_SOLID,
    PHASE_SUPER,
    PHASE_TO_INT,
    PHASE_VAPOR,
    LabelThresholds,
    label_phase,
    run_lattice_probe,
    run_pde_probe,
)


def run_trial(
    kappa: float,
    delta_omega: float,
    *,
    ic: str,
    seed: int,
    nx: int,
    nt: int,
    frames: int,
    n_sites: int,
    thr: LabelThresholds,
) -> dict:
    pde = run_pde_probe(
        kappa,
        delta_omega,
        nx=nx,
        nt=nt,
        ic=ic,
        seed=seed,
    )
    lat = run_lattice_probe(
        kappa,
        delta_omega,
        n_sites=n_sites,
        frames=frames,
        seed=seed,
    )
    phase, features = label_phase(pde, lat, thr=thr)
    return {
        "kappa": kappa,
        "delta_omega": delta_omega,
        "ic": ic,
        "seed": seed,
        "phase": phase,
        "phase_id": PHASE_TO_INT[phase],
        "mean_survival": pde["mean_survival"],
        "fluctuation_survival": pde["fluctuation_survival"],
        "structure_retention": pde.get("structure_retention"),
        "identity": lat["identity_preservation"],
        "burst_rate": lat["burst_rate"],
        "stability_score": lat["stability_score"],
        "drive_over_damp": pde["drive_over_damp"],
        **{f"feat_{k}": v for k, v in features.items()},
    }


def scan_point(
    kappa: float,
    delta_omega: float,
    *,
    ics: tuple[str, ...] = IC_CHOICES,
    n_seeds: int = 4,
    base_seed: int = 7,
    nx: int = 12,
    nt: int = 500,
    frames: int = 80,
    n_sites: int = 40,
    thr: LabelThresholds = LABEL_THRESHOLDS,
) -> dict:
    ic_offset = {"helical": 0, "hopfion": 3, "tetrahedral": 7, "uniform": 11}
    trials = []
    for ic in ics:
        for s in range(n_seeds):
            trials.append(
                run_trial(
                    kappa,
                    delta_omega,
                    ic=ic,
                    seed=base_seed + s * 19 + ic_offset.get(ic, 0),
                    nx=nx,
                    nt=nt,
                    frames=frames,
                    n_sites=n_sites,
                    thr=thr,
                )
            )
    phases = [t["phase"] for t in trials]
    counts = Counter(phases)
    n_phases = len(counts)
    # majority phase
    majority = counts.most_common(1)[0][0] if counts else None
    majority_frac = counts[majority] / max(1, len(trials)) if majority else 0.0
    # coexistence scores
    coexistence = n_phases >= 2
    triple_like = n_phases >= 3
    # Shannon entropy of phase distribution (0 = unique attractor, high = multi)
    probs = np.array([counts[p] / len(trials) for p in counts], dtype=float)
    entropy = float(-np.sum(probs * np.log(probs + 1e-15))) if len(probs) else 0.0
    # IC-resolved: which ICs produce which phases
    by_ic: dict[str, dict] = {}
    for ic in ics:
        sub = [t for t in trials if t["ic"] == ic]
        c = Counter(t["phase"] for t in sub)
        by_ic[ic] = dict(c)

    return {
        "kappa": kappa,
        "delta_omega": delta_omega,
        "n_trials": len(trials),
        "phase_counts": dict(counts),
        "n_phases": n_phases,
        "majority_phase": majority,
        "majority_frac": majority_frac,
        "coexistence": coexistence,
        "triple_like": triple_like,
        "phase_entropy": entropy,
        "by_ic": by_ic,
        "trials": trials,
    }


def run_scan(
    *,
    kappa_min: float = 0.55,
    kappa_max: float = 1.10,
    n_kappa: int = 5,
    domega_min: float = 0.002,
    domega_max: float = 0.06,
    n_domega: int = 5,
    ics: tuple[str, ...] = IC_CHOICES,
    n_seeds: int = 4,
    nx: int = 12,
    nt: int = 500,
    frames: int = 80,
    n_sites: int = 40,
    base_seed: int = 7,
    thr: LabelThresholds = LABEL_THRESHOLDS,
) -> dict:
    kappas = np.linspace(kappa_min, kappa_max, n_kappa)
    domegas = np.geomspace(domega_min, domega_max, n_domega)

    cells = []
    total = n_kappa * n_domega
    done = 0
    for kappa in kappas:
        for dω in domegas:
            cell = scan_point(
                float(kappa),
                float(dω),
                ics=ics,
                n_seeds=n_seeds,
                base_seed=base_seed,
                nx=nx,
                nt=nt,
                frames=frames,
                n_sites=n_sites,
                thr=thr,
            )
            # drop bulky per-trial traces from cell summary for grid arrays
            cells.append(
                {
                    **{k: v for k, v in cell.items() if k != "trials"},
                    "trials": cell["trials"],  # keep full for JSON analysis
                }
            )
            done += 1
            tag = (
                "TRIPLE"
                if cell["triple_like"]
                else ("BI" if cell["coexistence"] else cell["majority_phase"])
            )
            print(
                f"  [{done}/{total}] κ={kappa:.3f} Δω={dω:.4f}  "
                f"n_ph={cell['n_phases']}  H={cell['phase_entropy']:.3f}  "
                f"counts={dict(cell['phase_counts'])}  → {tag}"
            )

    # Grids for plots
    n_ph_grid = np.zeros((n_domega, n_kappa), dtype=int)
    ent_grid = np.zeros((n_domega, n_kappa))
    maj_grid = np.zeros((n_domega, n_kappa), dtype=int)
    for cell in cells:
        # find indices
        j = int(np.argmin(np.abs(kappas - cell["kappa"])))
        i = int(np.argmin(np.abs(domegas - cell["delta_omega"])))
        n_ph_grid[i, j] = cell["n_phases"]
        ent_grid[i, j] = cell["phase_entropy"]
        maj = cell["majority_phase"]
        maj_grid[i, j] = PHASE_TO_INT.get(maj, -1)

    multi = [c for c in cells if c["coexistence"]]
    triple = [c for c in cells if c["triple_like"]]
    # best triple-like: max entropy then max n_phases
    best = None
    if cells:
        best = max(
            cells,
            key=lambda c: (c["n_phases"], c["phase_entropy"], -abs(c["majority_frac"] - 0.5)),
        )

    # Slim trials in top-level JSON for multi points only to keep size reasonable
    return {
        "mode": "triple_point_scan",
        "framing": (
            "Multi-attractor scan: distinct phase labels across IC×seed ensemble "
            "at fixed (κ, Δω). n_phases≥3 is triple-like coexistence; ≥2 is bistable."
        ),
        "axes": {
            "x": "kappa",
            "y": "delta_omega (log)",
        },
        "grid": {
            "kappas": kappas.tolist(),
            "domegas": domegas.tolist(),
            "n_kappa": n_kappa,
            "n_domega": n_domega,
        },
        "settings": {
            "ics": list(ics),
            "n_seeds": n_seeds,
            "nx": nx,
            "nt": nt,
            "frames": frames,
            "n_sites": n_sites,
            "base_seed": base_seed,
        },
        "thresholds": {
            k: getattr(thr, k) for k in thr.__dataclass_fields__
        },
        "cells": cells,
        "n_coexistence": len(multi),
        "n_triple_like": len(triple),
        "coexistence_points": [
            {
                "kappa": c["kappa"],
                "delta_omega": c["delta_omega"],
                "n_phases": c["n_phases"],
                "phase_counts": c["phase_counts"],
                "phase_entropy": c["phase_entropy"],
                "by_ic": c["by_ic"],
            }
            for c in multi
        ],
        "triple_like_points": [
            {
                "kappa": c["kappa"],
                "delta_omega": c["delta_omega"],
                "n_phases": c["n_phases"],
                "phase_counts": c["phase_counts"],
                "phase_entropy": c["phase_entropy"],
                "by_ic": c["by_ic"],
            }
            for c in triple
        ],
        "best_multi_attractor": (
            {
                "kappa": best["kappa"],
                "delta_omega": best["delta_omega"],
                "n_phases": best["n_phases"],
                "phase_counts": best["phase_counts"],
                "phase_entropy": best["phase_entropy"],
                "by_ic": best["by_ic"],
                "majority_phase": best["majority_phase"],
                "majority_frac": best["majority_frac"],
            }
            if best
            else None
        ),
        "arrays": {
            "n_phases": n_ph_grid.tolist(),
            "phase_entropy": ent_grid.tolist(),
            "majority_phase_id": maj_grid.tolist(),
        },
        "reference": {
            "kappa_doc": 0.85,
            "kappa_sim": 0.89,
            "e_over_pi": E / PI,
        },
    }


def _edges(vals: np.ndarray, geom: bool = False) -> np.ndarray:
    if len(vals) == 1:
        return np.array([vals[0] * 0.9, vals[0] * 1.1]) if geom else np.array(
            [vals[0] - 0.05, vals[0] + 0.05]
        )
    if geom:
        logv = np.log(vals)
        mids = 0.5 * (logv[:-1] + logv[1:])
        edges_log = np.concatenate(
            [[logv[0] - (mids[0] - logv[0])], mids, [logv[-1] + (logv[-1] - mids[-1])]]
        )
        return np.exp(edges_log)
    mids = 0.5 * (vals[:-1] + vals[1:])
    return np.concatenate(
        [[vals[0] - (mids[0] - vals[0])], mids, [vals[-1] + (vals[-1] - mids[-1])]]
    )


def plot_scan(data: dict, out_path: Path) -> None:
    kappas = np.asarray(data["grid"]["kappas"], dtype=float)
    domegas = np.asarray(data["grid"]["domegas"], dtype=float)
    n_ph = np.asarray(data["arrays"]["n_phases"], dtype=float)
    ent = np.asarray(data["arrays"]["phase_entropy"], dtype=float)
    maj = np.asarray(data["arrays"]["majority_phase_id"], dtype=float)

    x_e = _edges(kappas, geom=False)
    y_e = _edges(domegas, geom=True)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.5))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    def _cbar(cb):
        cb.ax.yaxis.set_tick_params(color="#c9d1d9")
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#c9d1d9")

    # n_phases
    ax = axes[0, 0]
    pcm = ax.pcolormesh(x_e, y_e, n_ph, cmap="YlOrRd", vmin=1, vmax=4, shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("n_phases in IC×seed ensemble")
    _cbar(fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.04))
    for kval in (0.85, 0.89):
        ax.axvline(kval, color="#8b949e", ls=":", lw=1.0)
    # mark triple-like
    for p in data.get("triple_like_points", []):
        ax.plot(p["kappa"], p["delta_omega"], "o", mfc="none", mec="#58a6ff", ms=12, mew=2)

    # entropy
    ax = axes[0, 1]
    pcm = ax.pcolormesh(x_e, y_e, ent, cmap="magma", shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("Phase entropy H (multi-attractor strength)")
    _cbar(fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.04))
    for p in data.get("coexistence_points", []):
        ax.plot(p["kappa"], p["delta_omega"], "x", color="#3fb950", ms=8, mew=1.5)

    # majority phase
    ax = axes[1, 0]
    cmap = ListedColormap(PHASE_COLORS)
    pcm = ax.pcolormesh(x_e, y_e, maj, cmap=cmap, vmin=-0.5, vmax=3.5, shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("Majority phase label")
    ax.legend(
        handles=[
            Patch(facecolor=PHASE_COLORS[i], edgecolor="#30363d", label=INT_TO_PHASE[i])
            for i in range(4)
        ],
        loc="lower right",
        fontsize=7,
        framealpha=0.85,
    )

    # bar: how many cells per n_phases
    ax = axes[1, 1]
    counts = Counter(c["n_phases"] for c in data["cells"])
    xs = sorted(counts)
    ax.bar(xs, [counts[x] for x in xs], color="#58a6ff", edgecolor="#30363d")
    ax.set_xlabel("n_phases")
    ax.set_ylabel("# grid cells")
    ax.set_title(
        f"coexistence={data['n_coexistence']}  triple-like={data['n_triple_like']}"
    )
    ax.set_xticks(xs)

    best = data.get("best_multi_attractor") or {}
    fig.suptitle(
        f"Triple-point / multi-attractor scan  |  "
        f"best κ={best.get('kappa', float('nan')):.3f} Δω={best.get('delta_omega', float('nan')):.4f}  "
        f"n_ph={best.get('n_phases')}  H={best.get('phase_entropy', float('nan')):.3f}  "
        f"counts={best.get('phase_counts')}",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def print_best(data: dict) -> None:
    best = data.get("best_multi_attractor")
    if not best:
        print("  BEST_MULTI_ATTRACTOR: (none)")
        return
    print(
        "  BEST_MULTI_ATTRACTOR: "
        f"κ={best['kappa']}  Δω={best['delta_omega']}  "
        f"n_phases={best['n_phases']}  H={best['phase_entropy']:.4f}  "
        f"counts={best['phase_counts']}  by_ic={best['by_ic']}  "
        f"majority={best['majority_phase']} ({best['majority_frac']:.0%})"
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description="Multi-attractor triple-point scan (phase coexistence by IC×seed)"
    )
    p.add_argument("--kappa-min", type=float, default=0.55)
    p.add_argument("--kappa-max", type=float, default=1.10)
    p.add_argument("--n-kappa", type=int, default=5)
    p.add_argument("--domega-min", type=float, default=0.002)
    p.add_argument("--domega-max", type=float, default=0.06)
    p.add_argument("--n-domega", type=int, default=5)
    p.add_argument("--n-seeds", type=int, default=4)
    p.add_argument("--nx", type=int, default=12)
    p.add_argument("--nt", type=int, default=500)
    p.add_argument("--frames", type=int, default=80)
    p.add_argument("--n-sites", type=int, default=40)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--quick", action="store_true")
    args = p.parse_args()

    if args.quick:
        args.n_kappa = 4
        args.n_domega = 4
        args.n_seeds = 3
        args.nx = 10
        args.nt = 280
        args.frames = 50
        args.n_sites = 28

    print("Triple-point / multi-attractor scan (interpretive)")
    print(
        f"  grid {args.n_kappa}×{args.n_domega}  "
        f"κ∈[{args.kappa_min},{args.kappa_max}]  "
        f"Δω∈[{args.domega_min},{args.domega_max}]  "
        f"seeds={args.n_seeds}  ICs={list(IC_CHOICES)}"
    )

    data = run_scan(
        kappa_min=args.kappa_min,
        kappa_max=args.kappa_max,
        n_kappa=args.n_kappa,
        domega_min=args.domega_min,
        domega_max=args.domega_max,
        n_domega=args.n_domega,
        n_seeds=args.n_seeds,
        nx=args.nx,
        nt=args.nt,
        frames=args.frames,
        n_sites=args.n_sites,
        base_seed=args.seed,
    )

    # JSON size: strip full trials from all cells except coexistence points
    slim = {**data, "cells": []}
    for c in data["cells"]:
        entry = {k: v for k, v in c.items() if k != "trials"}
        if c["coexistence"]:
            entry["trials"] = c["trials"]
        slim["cells"].append(entry)

    plot_path = OUTPUT_DIR / "triple_point_scan.png"
    plot_scan(data, plot_path)
    report = save_report("triple_point_scan", slim)

    print("\n--- multi-attractor summary ---")
    print(f"  coexistence cells: {data['n_coexistence']}")
    print(f"  triple-like cells: {data['n_triple_like']}")
    print_best(data)
    if data["triple_like_points"]:
        print("  triple-like points:")
        for p in data["triple_like_points"]:
            print(
                f"    κ={p['kappa']:.3f} Δω={p['delta_omega']:.4f}  "
                f"{p['phase_counts']}  by_ic={p['by_ic']}"
            )
    print(f"Wrote {plot_path}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
