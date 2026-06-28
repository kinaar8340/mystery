#!/usr/bin/env python3
"""Angular separation analysis with vortex_math_369 + toroidal_modulo9 enabled."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUTPUT_DIR, save_report

TOE_ROOT = Path.home() / "Projects" / "toe"
TARGET_ANGLES = (30.0, 60.0, 90.0)


def load_conduit_module():
    conduit_path = TOE_ROOT / "src" / "conduit.py"
    for p in (str(TOE_ROOT / "src"), str(TOE_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import torch  # noqa: F401
    except ImportError:
        return None, "torch not installed"
    spec = importlib.util.spec_from_file_location("toe_conduit", conduit_path)
    if spec is None or spec.loader is None:
        return None, "bad module spec"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return module, None


def helix_angles_deg(conduit, n_samples: int = 256, pol_indices: tuple[int, ...] = (0, 1, 2, 3)) -> dict:
    """Collect planar helix turning angles and consecutive sample separations."""
    import torch

    all_sep_deg: list[float] = []
    all_turn_deg: list[float] = []
    per_pol: dict = {}

    for pol in pol_indices:
        s_vals = np.linspace(0.05, float(conduit.max_depth), n_samples)
        positions = []
        for s in s_vals:
            pos = conduit.get_helix_3d(s, pol)
            if hasattr(pos, "detach"):
                pos = pos.detach().cpu().numpy()
            positions.append(pos[:3])
        positions = np.asarray(positions)

        centered = positions - positions.mean(axis=0)
        proj = centered[:, :2]
        angles = np.degrees(np.arctan2(proj[:, 1], proj[:, 0]))

        # Consecutive angular steps (wrapped)
        diffs = np.diff(angles)
        diffs = (diffs + 180) % 360 - 180
        turns = np.abs(diffs)

        # Pairwise separations (subsample for speed)
        idx = np.linspace(0, len(angles) - 1, min(64, len(angles)), dtype=int)
        sub = angles[idx]
        sep_list = []
        for i in range(len(sub)):
            for j in range(i + 1, len(sub)):
                d = abs(sub[i] - sub[j])
                d = min(d, 360 - d)
                sep_list.append(d)
        sep = np.asarray(sep_list)

        all_turn_deg.extend(turns.tolist())
        all_sep_deg.extend(sep.tolist())
        per_pol[f"pol_{pol}"] = {
            "mean_turn_deg": float(np.mean(turns)),
            "median_turn_deg": float(np.median(turns)),
            "mean_pairwise_sep_deg": float(np.mean(sep)),
        }

    return {
        "turn_angles_deg": all_turn_deg,
        "pairwise_sep_deg": all_sep_deg,
        "per_polarization": per_pol,
    }


def cluster_near_targets(values_deg: list[float], targets: tuple[float, ...] = TARGET_ANGLES, tol: float = 5.0) -> dict:
    arr = np.asarray(values_deg)
    buckets = {}
    for t in targets:
        mask = np.abs(arr - t) <= tol
        buckets[f"within_{int(tol)}deg_of_{int(t)}"] = {
            "count": int(mask.sum()),
            "fraction": float(mask.mean()),
            "mean_value": float(arr[mask].mean()) if mask.any() else None,
        }
    # Also check 3-6-9 tens-of-degrees axis
    tens = arr / 10.0
    for t in (3, 6, 9):
        mask = np.abs(tens - t) <= 0.5
        buckets[f"within_0.5_tens_of_{t}"] = {
            "count": int(mask.sum()),
            "fraction": float(mask.mean()),
        }
    return buckets


def plot_histogram(raw_by_label: dict[str, list[float]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, label in zip(axes, ("baseline", "vortex_369")):
        raw = raw_by_label.get(label, [])
        color = "#c9a227" if label == "vortex_369" else "#2a6f97"
        ax.hist(raw, bins=36, range=(0, 180), color=color, alpha=0.8)
        for t in TARGET_ANGLES:
            ax.axvline(t, color="#e63946", ls="--", lw=0.9, alpha=0.7)
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("Count")
        ax.set_title(f"{label}: pairwise separations")
    fig.suptitle("Conduit angular separations vs 30°/60°/90° targets")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def probe() -> dict:
    module, err = load_conduit_module()
    if module is None:
        return {"status": "skipped", "reason": err}

    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    RubikConeConduit = module.RubikConeConduit

    result_modes = {}
    raw_for_plot = {}
    for label, v369 in (("baseline", False), ("vortex_369", True)):
        conduit = RubikConeConduit(
            wg_base=351.5,
            kappa=0.85,
            braiding_target=0.754,
            toroidal_modulo9=True,
            vortex_math_369=v369,
            clifford_projection=True,
        ).to(device)
        ang = helix_angles_deg(conduit)
        raw_for_plot[label] = ang["pairwise_sep_deg"]
        stats = conduit.monitor_topological_winding(n_samples=128)
        result_modes[label] = {
            "pairwise_clustering": cluster_near_targets(ang["pairwise_sep_deg"]),
            "turn_clustering": cluster_near_targets(ang["turn_angles_deg"], tol=3.0),
            "per_polarization": ang["per_polarization"],
            "winding_stats": {k: float(v) if isinstance(v, (int, float)) else str(v) for k, v in stats.items()},
            "raw_pairwise_deg": ang["pairwise_sep_deg"][:500],  # trim for JSON
        }

    plot_path = OUTPUT_DIR / "conduit_angular_histogram.png"
    plot_histogram(raw_for_plot, plot_path)

    return {
        "status": "ok",
        "device": device,
        "meta_seeds": {"wg_base": 351.5, "kappa": 0.85, "braiding": 0.754},
        "modes": result_modes,
        "interpretation": (
            "vortex_math_369 modulates knot phase; check if 30/60/90 clustering increases vs baseline."
        ),
        "plot": str(plot_path),
    }


def main() -> int:
    result = probe()
    report_path = save_report("conduit_angular_probe", result)
    print("=== Conduit Angular Probe (369 + toroidal mod 9) ===")
    if result["status"] != "ok":
        print(f"Skipped: {result.get('reason')}")
    else:
        for label in ("baseline", "vortex_369"):
            cl = result["modes"][label]["pairwise_clustering"]
            print(f"{label}: frac within 5° of 30° = {cl['within_5deg_of_30']['fraction']:.3f}, "
                  f"60° = {cl['within_5deg_of_60']['fraction']:.3f}, "
                  f"90° = {cl['within_5deg_of_90']['fraction']:.3f}")
    print(f"Report: {report_path}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())