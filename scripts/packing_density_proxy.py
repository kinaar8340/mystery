#!/usr/bin/env python3
"""
Packing density proxy — negative melting-slope (ice density anomaly) analog.

=============================================================================
  NOT H₂O thermodynamics. Asks whether lower effective packing can ever be
  *more* stable than denser packing — the classic ice-floats signature.
=============================================================================

Proxies (computed on the twist field θ after fixed-horizon PDE + lattice lock)

  packing_grad   = mean(|∇θ|)              higher → denser / compressed
  packing_open   = 1 / (1 + packing_grad)  higher → more open / expanded
  island_radius  = correlation length proxy from structure / gradient scale
  packing_island = 1 / (island_radius + ε) higher → denser (small islands)
  locked_fraction= fraction of sites with |identity-like| local order proxy
                   (here: local twist near mean after gauge lock on lattice)

Minimal experiment
  Fix κ near solid/liquid edge; sweep IC scale / gauge / seed type that
  changes island size; plot stability_score vs packing_open; report slope
  and whether any bin has negative slope (open more stable).

Outputs
  outputs/packing_density_proxy.png
  outputs/packing_density_proxy_<timestamp>.json

Examples
  python scripts/packing_density_proxy.py
  python scripts/packing_density_proxy.py --quick
  python scripts/packing_density_proxy.py --kappa 0.95 --n-amp 12
  # Longer multi-κ scan (solid → liquid → vapor neighborhoods)
  python scripts/packing_density_proxy.py --multi-kappa
  python scripts/packing_density_proxy.py --multi-kappa --n-amp 12 --nt 900
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUTPUT_DIR, PI, R_RESIDUAL, save_report  # noqa: E402
from flux_hopf_lib.constants import theta_crit as theta_crit_fn  # noqa: E402
from flux_hopf_lib.quaternion.core import q_conj, q_mult, q_normalize, small_rotor  # noqa: E402
from flux_hopf_lib.simulation.relaxation import twist_pde_step  # noqa: E402

# Reuse IC constructors from water-phase suite
from water_phase_analog_sweep import (  # noqa: E402
    IC_CHOICES,
    make_ic,
    structure_power,
)


# ---------------------------------------------------------------------------
# Packing diagnostics on θ
# ---------------------------------------------------------------------------
def mean_abs_grad(theta: np.ndarray) -> float:
    """Mean |∇θ| over the torus — compression / denseness proxy."""
    g2 = (
        np.gradient(theta, axis=0) ** 2
        + np.gradient(theta, axis=1) ** 2
        + np.gradient(theta, axis=2) ** 2
    )
    return float(np.mean(np.sqrt(g2)))


def island_radius_proxy(theta: np.ndarray, eps: float = 1e-8) -> float:
    """
    Characteristic length ~ std(θ) / mean|∇θ| (dimensionless grid units).

    Large radius → extended / open domains; small → tight / dense features.
    """
    g = mean_abs_grad(theta)
    return float(np.std(theta) / max(g, eps))


def packing_proxies(theta: np.ndarray, locked_fraction: float = 0.0) -> dict:
    grad = mean_abs_grad(theta)
    r_isl = island_radius_proxy(theta)
    # open packing: low gradient, large islands
    packing_open = 1.0 / (1.0 + grad)
    packing_dense_grad = grad  # alias for clarity in plots
    packing_dense_island = 1.0 / (r_isl + 1e-6)
    return {
        "mean_abs_grad": grad,
        "island_radius": r_isl,
        "packing_open": packing_open,
        "packing_dense_grad": packing_dense_grad,
        "packing_dense_island": packing_dense_island,
        "locked_fraction": float(locked_fraction),
        "structure_power": structure_power(theta),
        "theta_std": float(np.std(theta)),
        "theta_mean": float(theta.mean()),
    }


# ---------------------------------------------------------------------------
# Dual probes (PDE + multi-site lattice) — same lineage as water_phase suite
# ---------------------------------------------------------------------------
def run_lattice_lock(
    kappa: float,
    delta_omega: float,
    *,
    n_sites: int = 48,
    frames: int = 100,
    omega_L: float = 0.025,
    seed: int = 7,
    identity_lock_thresh: float = 0.55,
) -> dict:
    rng = np.random.default_rng(seed)
    q = np.array([q_normalize(rng.standard_normal(4)) for _ in range(n_sites)])
    identity = np.array([q_normalize(rng.standard_normal(4)) for _ in range(n_sites)])
    identity0 = identity.copy()
    twist = np.zeros(n_sites)
    gauge_strength = float(kappa)
    omega_R = omega_L - float(delta_omega)
    t_crit = float(theta_crit_fn(kappa))
    total_bursts = 0
    id_hist: list[float] = []

    for _ in range(frames):
        dL, dR = small_rotor(omega_L), small_rotor(omega_R)
        for i in range(n_sites):
            q[i] = q_normalize(q_mult(q_mult(dL, q[i]), q_conj(dR)))
            twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))
        avg = float(np.mean(twist) % (2.0 * np.pi))
        ga = -gauge_strength * avg
        grot = np.array([np.cos(ga), 0.0, 0.0, np.sin(ga)])
        for i in range(n_sites):
            q[i] = q_normalize(q_mult(q[i], grot))
            identity[i] = q_normalize(q_mult(identity[i], grot))
        for i in range(n_sites):
            if twist[i] > t_crit:
                q[i] = q_normalize(0.3 * np.array([1.0, 0.0, 0.0, 0.0]) + 0.7 * q[i])
                twist[i] *= 0.15
                total_bursts += 1
        cos = np.abs(np.sum(identity * identity0, axis=1))
        id_hist.append(float(np.mean(cos)))

    id_tail = float(np.mean(id_hist[-max(10, frames // 5) :]))
    burst_rate = total_bursts / max(1, frames * n_sites)
    stability = id_tail / (1.0 + 10.0 * burst_rate)
    # per-site lock at end
    cos_end = np.abs(np.sum(identity * identity0, axis=1))
    locked_fraction = float(np.mean(cos_end >= identity_lock_thresh))
    return {
        "identity": id_tail,
        "burst_rate": burst_rate,
        "stability_score": float(stability),
        "locked_fraction": locked_fraction,
    }


def run_pde_field(
    kappa: float,
    delta_omega: float,
    *,
    nx: int = 12,
    nt: int = 600,
    dt: float = 0.001,
    D: float = 0.05,
    ic: str = "helical",
    ic_amplitude: float = 1.2,
    seed: int = 42,
) -> dict:
    """Evolve θ; return packing proxies + survival S + field stability."""
    t_crit = float(theta_crit_fn(kappa))
    # Build IC with amplitude scaling for island-size sweep
    if ic == "helical":
        from water_phase_analog_sweep import ic_helical

        theta = ic_helical(nx, amplitude=ic_amplitude)
    elif ic == "hopfion":
        from water_phase_analog_sweep import ic_hopfion

        theta = ic_hopfion(nx, amplitude=max(0.5, ic_amplitude * 2.0))
    elif ic == "tetrahedral":
        from water_phase_analog_sweep import ic_tetrahedral

        theta = ic_tetrahedral(nx, amplitude=ic_amplitude)
    else:
        theta = make_ic(ic, nx, seed=seed)
        if ic_amplitude != 1.0:
            m = float(theta.mean())
            theta = m + ic_amplitude * (theta - m)

    theta0_mean = float(theta.mean())
    theta0_std = float(theta.std())
    struct0 = structure_power(theta)
    pack0 = packing_proxies(theta)
    burst_risk = 0
    n_vox = nx**3
    for _ in range(nt):
        burst_risk += int(np.sum(theta > 0.95 * t_crit))
        theta = twist_pde_step(
            theta,
            dt=dt,
            D=D,
            kappa=kappa,
            delta_omega=delta_omega,
            theta_crit=t_crit,
            nx=nx,
        )
    S = float(theta.mean() / theta0_mean) if abs(theta0_mean) > 1e-12 else 0.0
    F = float(theta.std() / theta0_std) if theta0_std > 1e-12 else 0.0
    struct = structure_power(theta)
    struct_ret = float(struct / struct0) if struct0 > 1e-18 else 0.0
    pack = packing_proxies(theta)
    # Field stability: retains structure while not exploding gradients
    # High when structure_retention and packing_open both decent
    field_stability = float(
        struct_ret * pack["packing_open"] * (1.0 + F) / (1.0 + pack["mean_abs_grad"])
    )
    return {
        "theta": theta,
        "mean_survival": S,
        "fluctuation_survival": F,
        "structure_retention": struct_ret,
        "field_stability": field_stability,
        "final_mean": float(theta.mean()),
        "burst_risk": burst_risk / max(1, nt * n_vox),
        "pack0": pack0,
        "pack": pack,
    }


def run_point(
    kappa: float,
    delta_omega: float,
    *,
    ic: str,
    ic_amplitude: float,
    nx: int,
    nt: int,
    frames: int,
    n_sites: int,
    seed: int,
) -> dict:
    pde = run_pde_field(
        kappa,
        delta_omega,
        nx=nx,
        nt=nt,
        ic=ic,
        ic_amplitude=ic_amplitude,
        seed=seed,
    )
    # Lattice detuning mildly coupled to packing (denser field → more stress)
    pack = pde["pack"]
    dω_eff = float(delta_omega) * (1.0 + 2.0 * pack["mean_abs_grad"])
    lat = run_lattice_lock(
        kappa, dω_eff, n_sites=n_sites, frames=frames, seed=seed
    )
    pack_out = {**pack, "locked_fraction": lat["locked_fraction"]}
    # Composite: field + lattice (lattice alone is nearly IC-flat without coupling)
    composite_stability = 0.55 * pde["field_stability"] + 0.45 * lat["stability_score"]
    return {
        "kappa": kappa,
        "delta_omega": delta_omega,
        "delta_omega_eff": dω_eff,
        "ic": ic,
        "ic_amplitude": ic_amplitude,
        "mean_survival": pde["mean_survival"],
        "fluctuation_survival": pde["fluctuation_survival"],
        "structure_retention": pde["structure_retention"],
        "field_stability": pde["field_stability"],
        "final_mean": pde["final_mean"],
        "burst_risk_pde": pde["burst_risk"],
        "composite_stability": float(composite_stability),
        **{f"lat_{k}": v for k, v in lat.items()},
        **pack_out,
        # primary y used in slope analysis
        "stability_score": float(composite_stability),
        "delta_pct_vs_R": 100.0 * abs(pde["mean_survival"] - R_RESIDUAL) / abs(R_RESIDUAL),
    }


# ---------------------------------------------------------------------------
# Sweep + slope analysis
# ---------------------------------------------------------------------------
PROXY_DEFS = {
    "packing_open": "1 / (1 + mean|∇θ|)  — high = open / expanded",
    "packing_dense_grad": "mean|∇θ|  — high = dense / compressed",
    "island_radius": "std(θ) / mean|∇θ|",
    "packing_dense_island": "1 / (island_radius + ε)",
    "locked_fraction": "fraction of lattice sites with |⟨q,q₀⟩| ≥ 0.55",
    "stability_score": "0.55·field_stability + 0.45·lattice_stability (packing-coupled)",
}

# Default multi-κ ladder: solid-ish → κ_doc → κ_sim → liquid → soft vapor
DEFAULT_KAPPA_LADDER = (0.55, 0.70, 0.85, 0.89, 0.95, 1.05, 1.15)


def run_sweep(
    *,
    kappa: float = 0.90,
    delta_omega: float = 0.008,
    amps: np.ndarray | None = None,
    ics: tuple[str, ...] = ("helical", "hopfion", "tetrahedral"),
    nx: int = 12,
    nt: int = 600,
    frames: int = 100,
    n_sites: int = 48,
    seed: int = 7,
    quiet: bool = False,
) -> dict:
    if amps is None:
        amps = np.linspace(0.4, 2.4, 9)

    rows: list[dict] = []
    total = len(amps) * len(ics)
    done = 0
    for ic in ics:
        for amp in amps:
            row = run_point(
                kappa,
                delta_omega,
                ic=ic,
                ic_amplitude=float(amp),
                nx=nx,
                nt=nt,
                frames=frames,
                n_sites=n_sites,
                seed=seed,
            )
            rows.append(row)
            done += 1
            if not quiet and (done % max(1, total // 8) == 0 or done == total):
                print(
                    f"  [{done}/{total}] κ={kappa:.3f} ic={ic:12s} amp={amp:.2f}  "
                    f"open={row['packing_open']:.4f}  "
                    f"stab={row['stability_score']:.4f}  S={row['mean_survival']:.4f}"
                )

    analysis = analyze_negative_slope(rows)
    return {
        "mode": "packing_density_proxy",
        "framing": (
            "Interpretive packing proxies on twist field + lattice lock. "
            "Negative slope of stability vs packing_open would be an ice-density "
            "anomaly analog (expanded lock more stable)."
        ),
        "fixed": {"kappa": kappa, "delta_omega": delta_omega},
        "amps": amps.tolist(),
        "ics": list(ics),
        "settings": {"nx": nx, "nt": nt, "frames": frames, "n_sites": n_sites, "seed": seed},
        "proxy_defs": PROXY_DEFS,
        "rows": rows,
        "analysis": analysis,
    }


def run_multi_kappa_sweep(
    *,
    kappas: tuple[float, ...] | list[float] = DEFAULT_KAPPA_LADDER,
    delta_omega: float = 0.008,
    amps: np.ndarray | None = None,
    ics: tuple[str, ...] = ("helical", "hopfion", "tetrahedral"),
    nx: int = 14,
    nt: int = 900,
    frames: int = 140,
    n_sites: int = 48,
    seed: int = 7,
) -> dict:
    """
    Longer packing sweep across multiple κ (solid / liquid / vapor neighborhoods).

    Per-κ amplitude×IC grid → slope/pearson; then κ-dependent anomaly map.
    """
    if amps is None:
        amps = np.linspace(0.35, 2.6, 12)

    slices: list[dict] = []
    all_rows: list[dict] = []
    for kappa in kappas:
        print(f"\n=== κ = {kappa:.3f} ===")
        sl = run_sweep(
            kappa=float(kappa),
            delta_omega=delta_omega,
            amps=amps,
            ics=ics,
            nx=nx,
            nt=nt,
            frames=frames,
            n_sites=n_sites,
            seed=seed,
            quiet=False,
        )
        a = sl["analysis"]
        slices.append(
            {
                "kappa": float(kappa),
                "analysis": a,
                "n_rows": len(sl["rows"]),
                "pearson_stab_vs_open": a.get("pearson_stab_vs_open"),
                "global_slope_stab_vs_open": a.get("global_slope_stab_vs_open"),
                "has_negative_slope_region": a.get("has_negative_slope_region"),
                "per_ic": a.get("per_ic", {}),
            }
        )
        all_rows.extend(sl["rows"])

    # Robust anomaly score per κ:
    #   anomaly_score = f_open * mean(positive slopes)
    # where f_open = fraction of ICs with slope > 0 (open more stable).
    # Also track helical specifically (strongest anomaly family so far).
    anomaly_by_kappa = []
    for sl in slices:
        per = sl.get("per_ic") or {}
        if not per:
            anomaly_by_kappa.append(
                {
                    "kappa": sl["kappa"],
                    "n_ic": 0,
                    "n_open_favored": 0,
                    "n_dense_favored": 0,
                    "anomaly_fraction": float("nan"),
                    "mean_positive_slope": float("nan"),
                    "anomaly_score": float("nan"),
                    "helical_slope": float("nan"),
                    "helical_open_favored": False,
                }
            )
            continue
        slopes = [float(v.get("slope_stab_vs_open", 0.0)) for v in per.values()]
        # Ignore near-flat slopes |s| < eps as noise (neither open nor dense)
        slope_eps = 1e-4
        pos = [s for s in slopes if s > slope_eps]
        n_open = len(pos)
        n_dense = sum(1 for s in slopes if s < -slope_eps)
        f_open = n_open / max(1, len(per))
        mean_pos = float(np.mean(pos)) if pos else 0.0
        # Robust score: breadth × strength of open-favored signal
        anomaly_score = float(f_open * mean_pos)
        hel = per.get("helical", {})
        hel_slope = float(hel.get("slope_stab_vs_open", float("nan"))) if hel else float("nan")
        anomaly_by_kappa.append(
            {
                "kappa": sl["kappa"],
                "n_ic": len(per),
                "n_open_favored": n_open,
                "n_dense_favored": n_dense,
                "anomaly_fraction": f_open,
                "mean_positive_slope": mean_pos,
                "anomaly_score": anomaly_score,
                "mean_all_slopes": float(np.mean(slopes)),
                "helical_slope": hel_slope,
                "helical_open_favored": bool(hel_slope == hel_slope and hel_slope > 0),
                "global_slope": sl.get("global_slope_stab_vs_open"),
                "pearson": sl.get("pearson_stab_vs_open"),
                "per_ic_slopes": {k: v.get("slope_stab_vs_open") for k, v in per.items()},
            }
        )

    # Best κ: max robust anomaly_score, then helical slope as tie-break
    def _rank_key(item: dict) -> tuple:
        score = item.get("anomaly_score")
        if score is None or (isinstance(score, float) and score != score):
            score = -1e9
        hel = item.get("helical_slope")
        if hel is None or (isinstance(hel, float) and hel != hel):
            hel = -1e9
        return (score, hel)

    best = max(anomaly_by_kappa, key=_rank_key) if anomaly_by_kappa else None

    # Helical-positive contiguous region on the κ ladder
    helical_positive_kappas = [
        a["kappa"] for a in anomaly_by_kappa if a.get("helical_open_favored")
    ]
    helical_region = None
    if helical_positive_kappas:
        helical_region = {
            "kappa_min": min(helical_positive_kappas),
            "kappa_max": max(helical_positive_kappas),
            "kappas": helical_positive_kappas,
            "n": len(helical_positive_kappas),
        }

    return {
        "mode": "packing_density_multi_kappa",
        "framing": (
            "Multi-κ packing sweep: does the open-favored (ice-anomaly) slope "
            "appear only near solid/liquid edge, or elsewhere?"
        ),
        "anomaly_score_def": (
            "anomaly_score = (fraction of ICs with slope>0) × (mean of positive slopes); "
            "helical_slope tracked separately as strongest family signal"
        ),
        "kappas": list(kappas),
        "delta_omega": delta_omega,
        "amps": amps.tolist(),
        "ics": list(ics),
        "settings": {"nx": nx, "nt": nt, "frames": frames, "n_sites": n_sites, "seed": seed},
        "proxy_defs": PROXY_DEFS,
        "slices": slices,
        "rows": all_rows,
        "anomaly_by_kappa": anomaly_by_kappa,
        "best_anomaly_kappa": best,
        "helical_positive_region": helical_region,
    }


def analyze_negative_slope(rows: list[dict], n_bins: int = 6) -> dict:
    """
    Global Pearson r and binned mean slope: stability vs packing_open.

    Also per-IC slopes. Flag negative_slope_region if any mid-bin pair
    has Δstab / Δopen < 0 with enough points.
    """
    if len(rows) < 4:
        return {"ok": False, "reason": "too few points"}

    open_p = np.array([r["packing_open"] for r in rows], dtype=float)
    stab = np.array([r["stability_score"] for r in rows], dtype=float)
    S = np.array([r["mean_survival"] for r in rows], dtype=float)

    def _pearson(a: np.ndarray, b: np.ndarray) -> float:
        if len(a) < 3 or np.std(a) < 1e-12 or np.std(b) < 1e-12:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    # Linear slope via least squares: stab = m * open + c
    A = np.vstack([open_p, np.ones_like(open_p)]).T
    m_stab, c_stab = np.linalg.lstsq(A, stab, rcond=None)[0]
    m_S, c_S = np.linalg.lstsq(A, S, rcond=None)[0]

    # Binned means
    order = np.argsort(open_p)
    open_s, stab_s = open_p[order], stab[order]
    edges = np.linspace(open_s.min(), open_s.max(), n_bins + 1)
    bin_open, bin_stab, bin_n = [], [], []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (open_s >= lo) & (open_s <= hi if i == n_bins - 1 else open_s < hi)
        if mask.sum() == 0:
            continue
        bin_open.append(float(open_s[mask].mean()))
        bin_stab.append(float(stab_s[mask].mean()))
        bin_n.append(int(mask.sum()))

    neg_segments = []
    for i in range(len(bin_open) - 1):
        d_open = bin_open[i + 1] - bin_open[i]
        d_stab = bin_stab[i + 1] - bin_stab[i]
        if abs(d_open) < 1e-12:
            continue
        slope = d_stab / d_open
        if slope < 0 and bin_n[i] >= 1 and bin_n[i + 1] >= 1:
            neg_segments.append(
                {
                    "open_lo": bin_open[i],
                    "open_hi": bin_open[i + 1],
                    "slope": float(slope),
                    "n_lo": bin_n[i],
                    "n_hi": bin_n[i + 1],
                }
            )

    per_ic = {}
    for ic in sorted({r["ic"] for r in rows}):
        sub = [r for r in rows if r["ic"] == ic]
        o = np.array([r["packing_open"] for r in sub])
        s = np.array([r["stability_score"] for r in sub])
        if len(sub) >= 3 and np.std(o) > 1e-12:
            A_ic = np.vstack([o, np.ones_like(o)]).T
            m_ic, _ = np.linalg.lstsq(A_ic, s, rcond=None)[0]
            per_ic[ic] = {
                "slope_stab_vs_open": float(m_ic),
                "pearson_r": _pearson(o, s),
                "n": len(sub),
            }

    return {
        "ok": True,
        "pearson_stab_vs_open": _pearson(open_p, stab),
        "pearson_S_vs_open": _pearson(open_p, S),
        "global_slope_stab_vs_open": float(m_stab),
        "global_slope_S_vs_open": float(m_S),
        "intercept_stab": float(c_stab),
        "binned_open": bin_open,
        "binned_stability": bin_stab,
        "binned_n": bin_n,
        "negative_slope_segments": neg_segments,
        "has_negative_slope_region": len(neg_segments) > 0,
        "per_ic": per_ic,
        "interpretation": (
            "Positive slope of stability vs packing_open (open more stable) is the "
            "ice-density anomaly analog. Negative slope = denser locks more stable "
            "(ordinary solids)."
        ),
    }


def plot_multi_kappa(data: dict, out_path: Path) -> None:
    """κ ladder: per-IC slopes heatmap + anomaly fraction + global pearson."""
    slices = data["slices"]
    ics = list(data["ics"])
    kappas = [s["kappa"] for s in slices]
    colors = {
        "helical": "#58a6ff",
        "hopfion": "#3fb950",
        "tetrahedral": "#d29922",
        "uniform": "#f85149",
    }

    # slope matrix [ic, kappa]
    mat = np.full((len(ics), len(kappas)), np.nan)
    for j, sl in enumerate(slices):
        per = sl.get("per_ic") or {}
        for i, ic in enumerate(ics):
            if ic in per:
                mat[i, j] = per[ic]["slope_stab_vs_open"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")
        ax.grid(True, alpha=0.25, color="#30363d")

    ax = axes[0, 0]
    # diverging cmap: blue = open-favored (anomaly), red = dense-favored
    vmax = np.nanmax(np.abs(mat)) if np.any(np.isfinite(mat)) else 1.0
    vmax = max(float(vmax), 1e-6)
    im = ax.imshow(mat, aspect="auto", cmap="RdBu", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(kappas)))
    ax.set_xticklabels([f"{k:.2f}" for k in kappas], rotation=30, ha="right")
    ax.set_yticks(range(len(ics)))
    ax.set_yticklabels(ics)
    ax.set_xlabel("κ")
    ax.set_title("per-IC slope(stab vs packing_open)\nblue = open-favored (anomaly)")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.yaxis.set_tick_params(color="#c9d1d9")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#c9d1d9")

    ax = axes[0, 1]
    abk = data["anomaly_by_kappa"]
    # Highlight helical-positive κ band
    hreg = data.get("helical_positive_region")
    if hreg and hreg.get("kappa_min") is not None:
        ax.axvspan(
            hreg["kappa_min"] - 0.02,
            hreg["kappa_max"] + 0.02,
            color="#58a6ff",
            alpha=0.12,
            label="helical open-favored",
        )
    ax.plot(
        [a["kappa"] for a in abk],
        [a["anomaly_fraction"] for a in abk],
        "o-",
        color="#58a6ff",
        lw=1.8,
        label="f_open",
    )
    # Robust score (normalized for dual axis readability)
    scores = [a.get("anomaly_score") or 0.0 for a in abk]
    smax = max(scores) if scores and max(scores) > 0 else 1.0
    ax2 = ax.twinx()
    ax2.plot(
        [a["kappa"] for a in abk],
        scores,
        "s--",
        color="#3fb950",
        lw=1.4,
        label="anomaly_score",
    )
    ax2.set_ylabel("anomaly_score = f_open × ⟨slope₊⟩", color="#3fb950")
    ax2.tick_params(colors="#3fb950")
    ax.axhline(0.5, color="#8b949e", ls="--", lw=1.0)
    ax.set_xlabel("κ")
    ax.set_ylabel("fraction of ICs with slope > 0")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Anomaly fraction + robust score vs κ")
    for kval, lab in [(0.85, "κ_doc"), (0.89, "κ_sim")]:
        ax.axvline(kval, color="#8b949e", ls=":", lw=0.9, alpha=0.8)
    # merge legends
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="best")

    ax = axes[1, 0]
    if hreg and hreg.get("kappa_min") is not None:
        ax.axvspan(
            hreg["kappa_min"] - 0.02,
            hreg["kappa_max"] + 0.02,
            color="#58a6ff",
            alpha=0.12,
            zorder=0,
        )
    for ic in ics:
        ys = []
        for sl in slices:
            per = sl.get("per_ic") or {}
            ys.append(per[ic]["slope_stab_vs_open"] if ic in per else np.nan)
        lw = 2.4 if ic == "helical" else 1.4
        ms = 7 if ic == "helical" else 5
        ax.plot(
            kappas,
            ys,
            "o-",
            color=colors.get(ic, "#c9d1d9"),
            label=ic + (" ★" if ic == "helical" else ""),
            ms=ms,
            lw=lw,
            zorder=5 if ic == "helical" else 3,
        )
    ax.axhline(0.0, color="#8b949e", ls="--", lw=1.0)
    # mark helical-positive points
    for a in abk:
        if a.get("helical_open_favored"):
            ax.scatter(
                [a["kappa"]],
                [a.get("helical_slope")],
                s=120,
                facecolors="none",
                edgecolors="#58a6ff",
                linewidths=2.0,
                zorder=6,
            )
    ax.set_xlabel("κ")
    ax.set_ylabel("slope(stab vs open)")
    ax.set_title("Per-IC slopes  (ring = helical open-favored)")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    # scatter all rows colored by κ
    rows = data["rows"]
    k_vals = np.array([r["kappa"] for r in rows])
    sc = ax.scatter(
        [r["packing_open"] for r in rows],
        [r["stability_score"] for r in rows],
        c=k_vals,
        cmap="viridis",
        s=18,
        alpha=0.75,
        edgecolors="none",
    )
    ax.set_xlabel("packing_open")
    ax.set_ylabel("stability_score")
    ax.set_title("All points colored by κ")
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("κ", color="#c9d1d9")
    cb.ax.yaxis.set_tick_params(color="#c9d1d9")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#c9d1d9")

    best = data.get("best_anomaly_kappa") or {}
    hreg = data.get("helical_positive_region") or {}
    fig.suptitle(
        f"Multi-κ packing  |  best score κ≈{best.get('kappa', float('nan')):.3f}  "
        f"score={best.get('anomaly_score', float('nan')):.4f}  "
        f"f_open={best.get('anomaly_fraction', float('nan')):.2f}  "
        f"helical+ band κ∈[{hreg.get('kappa_min', float('nan')):.2f},"
        f"{hreg.get('kappa_max', float('nan')):.2f}]",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_results(data: dict, out_path: Path) -> None:
    rows = data["rows"]
    analysis = data["analysis"]
    ics = sorted({r["ic"] for r in rows})
    colors = {
        "helical": "#58a6ff",
        "hopfion": "#3fb950",
        "tetrahedral": "#d29922",
        "uniform": "#f85149",
    }

    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")
        ax.grid(True, alpha=0.25, color="#30363d")

    # stability (composite) vs packing_open
    ax = axes[0, 0]
    for ic in ics:
        sub = [r for r in rows if r["ic"] == ic]
        ax.scatter(
            [r["packing_open"] for r in sub],
            [r["stability_score"] for r in sub],
            c=colors.get(ic, "#c9d1d9"),
            label=ic,
            s=36,
            alpha=0.9,
            edgecolors="#30363d",
        )
    if analysis.get("ok") and analysis.get("binned_open"):
        ax.plot(
            analysis["binned_open"],
            analysis["binned_stability"],
            "w--",
            lw=1.2,
            alpha=0.7,
            label="binned mean",
        )
    m = analysis.get("global_slope_stab_vs_open", float("nan"))
    ax.set_xlabel("packing_open = 1/(1+mean|∇θ|)")
    ax.set_ylabel("stability_score")
    ax.set_title(f"Stability vs open packing  (slope={m:.3g})")
    ax.legend(fontsize=7, loc="best")

    # S vs packing_open
    ax = axes[0, 1]
    for ic in ics:
        sub = [r for r in rows if r["ic"] == ic]
        ax.scatter(
            [r["packing_open"] for r in sub],
            [r["mean_survival"] for r in sub],
            c=colors.get(ic, "#c9d1d9"),
            label=ic,
            s=36,
            alpha=0.9,
            edgecolors="#30363d",
        )
    ax.set_xlabel("packing_open")
    ax.set_ylabel("mean survival S")
    ax.set_title(f"S vs open packing  (slope={analysis.get('global_slope_S_vs_open', float('nan')):.3g})")
    ax.legend(fontsize=7)

    # amp → packing + stability
    ax = axes[1, 0]
    for ic in ics:
        sub = sorted([r for r in rows if r["ic"] == ic], key=lambda r: r["ic_amplitude"])
        ax.plot(
            [r["ic_amplitude"] for r in sub],
            [r["packing_open"] for r in sub],
            "o-",
            color=colors.get(ic, "#c9d1d9"),
            label=f"{ic} open",
            ms=4,
        )
    ax.set_xlabel("IC amplitude (island-size knob)")
    ax.set_ylabel("packing_open")
    ax.set_title("How amplitude tunes packing")
    ax.legend(fontsize=7)

    ax = axes[1, 1]
    for ic in ics:
        sub = sorted([r for r in rows if r["ic"] == ic], key=lambda r: r["ic_amplitude"])
        ax.plot(
            [r["ic_amplitude"] for r in sub],
            [r["stability_score"] for r in sub],
            "s-",
            color=colors.get(ic, "#c9d1d9"),
            label=ic,
            ms=4,
        )
    ax.set_xlabel("IC amplitude")
    ax.set_ylabel("stability_score")
    ax.set_title("Stability vs amplitude")
    ax.legend(fontsize=7)

    m = analysis.get("global_slope_stab_vs_open", float("nan"))
    r_p = analysis.get("pearson_stab_vs_open", float("nan"))
    open_favored = m > 0 if m == m else False  # nan-safe
    fig.suptitle(
        f"Packing density proxy  κ={data['fixed']['kappa']:.3f}  Δω={data['fixed']['delta_omega']:.4f}  |  "
        f"r(stab,open)={r_p:.3f}  slope={m:.3g}  "
        f"{'OPEN-FAVORED (anomaly-like)' if open_favored else 'dense-favored / mixed'}",
        color="#3fb950" if open_favored else "#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def print_best_anomaly_config(data: dict) -> None:
    """One-line recipe for the best anomaly configuration (multi-κ or single)."""
    best = data.get("best_anomaly_kappa")
    if not best and data.get("mode") == "packing_density_proxy":
        # synthesize from single-κ analysis
        a = data.get("analysis") or {}
        per = a.get("per_ic") or {}
        pos = {
            ic: v["slope_stab_vs_open"]
            for ic, v in per.items()
            if v.get("slope_stab_vs_open", 0) > 1e-4
        }
        best = {
            "kappa": data.get("fixed", {}).get("kappa"),
            "anomaly_score": (
                (len(pos) / max(1, len(per))) * float(np.mean(list(pos.values())))
                if pos
                else 0.0
            ),
            "anomaly_fraction": len(pos) / max(1, len(per)) if per else 0.0,
            "helical_slope": (per.get("helical") or {}).get("slope_stab_vs_open"),
            "per_ic_slopes": {ic: v.get("slope_stab_vs_open") for ic, v in per.items()},
        }
    if not best:
        print("  BEST_ANOMALY: (none)")
        return
    kappa = best.get("kappa")
    dω = data.get("delta_omega") or data.get("fixed", {}).get("delta_omega")
    ics = data.get("ics", [])
    settings = data.get("settings") or {}
    open_ics = [
        ic
        for ic, s in (best.get("per_ic_slopes") or {}).items()
        if s is not None and s > 1e-4
    ]
    print(
        "  BEST_ANOMALY: "
        f"κ={kappa}  Δω={dω}  score={best.get('anomaly_score')}  "
        f"f_open={best.get('anomaly_fraction')}  "
        f"helical_slope={best.get('helical_slope')}  "
        f"open_ICs={open_ics or '—'}  "
        f"nx={settings.get('nx')} nt={settings.get('nt')}  "
        f"ics={list(ics)}"
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Packing density proxy (ice density anomaly analog)")
    p.add_argument("--kappa", type=float, default=0.90)
    p.add_argument("--domega", type=float, default=0.008)
    p.add_argument("--n-amp", type=int, default=9)
    p.add_argument("--amp-min", type=float, default=0.4)
    p.add_argument("--amp-max", type=float, default=2.4)
    p.add_argument("--nx", type=int, default=12)
    p.add_argument("--nt", type=int, default=600)
    p.add_argument("--frames", type=int, default=100)
    p.add_argument("--n-sites", type=int, default=48)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--quick", action="store_true")
    p.add_argument(
        "--multi-kappa",
        action="store_true",
        help="Longer sweep across a κ ladder (solid/liquid/vapor neighborhoods)",
    )
    p.add_argument(
        "--kappas",
        type=str,
        default="",
        help="Comma-separated κ list for --multi-kappa (default ladder)",
    )
    p.add_argument(
        "--ics",
        type=str,
        default="helical,hopfion,tetrahedral",
        help="Comma-separated IC names",
    )
    args = p.parse_args()

    if args.quick and args.multi_kappa:
        args.n_amp = 5
        args.nx = 10
        args.nt = 280
        args.frames = 40
        args.n_sites = 28
        args.amp_min = 0.4
        args.amp_max = 2.2
    elif args.quick:
        args.n_amp = 5
        args.nx = 10
        args.nt = 300
        args.frames = 50
        args.n_sites = 32
    elif args.multi_kappa:
        # longer defaults when multi-κ without --quick
        if args.n_amp == 9:
            args.n_amp = 12
        if args.nx == 12:
            args.nx = 14
        if args.nt == 600:
            args.nt = 900
        if args.frames == 100:
            args.frames = 140
        if args.amp_max == 2.4:
            args.amp_min = 0.35
            args.amp_max = 2.6

    ics = tuple(s.strip() for s in args.ics.split(",") if s.strip())
    for ic in ics:
        if ic not in IC_CHOICES:
            print(f"Unknown IC {ic!r}; choose from {IC_CHOICES}")
            return 1

    amps = np.linspace(args.amp_min, args.amp_max, args.n_amp)

    if args.multi_kappa:
        if args.kappas.strip():
            kappas = tuple(float(x) for x in args.kappas.split(",") if x.strip())
        elif args.quick:
            kappas = (0.70, 0.85, 0.89, 1.05)
        else:
            kappas = DEFAULT_KAPPA_LADDER

        print("Packing density MULTI-κ sweep (interpretive — not H₂O thermo)")
        print(f"  kappas={kappas}  Δω={args.domega}  amps={args.n_amp}  ics={ics}")
        print(f"  nx={args.nx} nt={args.nt} frames={args.frames}")

        data = run_multi_kappa_sweep(
            kappas=kappas,
            delta_omega=args.domega,
            amps=amps,
            ics=ics,
            nx=args.nx,
            nt=args.nt,
            frames=args.frames,
            n_sites=args.n_sites,
            seed=args.seed,
        )
        plot_path = OUTPUT_DIR / "packing_density_multi_kappa.png"
        plot_multi_kappa(data, plot_path)
        report = save_report("packing_density_multi_kappa", data)

        print("\n--- multi-κ anomaly summary ---")
        print("  score = f_open × mean(positive slopes)  |  ★ = helical open-favored")
        for a in data["anomaly_by_kappa"]:
            star = "★" if a.get("helical_open_favored") else " "
            print(
                f"  {star} κ={a['kappa']:.3f}  open={a['n_open_favored']}/{a['n_ic']}  "
                f"f={a['anomaly_fraction']:.2f}  ⟨slope₊⟩={a.get('mean_positive_slope', 0):.4f}  "
                f"score={a.get('anomaly_score', 0):.4f}  "
                f"helical={a.get('helical_slope')}"
            )
        best = data.get("best_anomaly_kappa")
        if best:
            print(
                f"  best score κ≈{best['kappa']:.3f}  "
                f"score={best.get('anomaly_score'):.4f}  "
                f"f_open={best.get('anomaly_fraction'):.2f}"
            )
        hreg = data.get("helical_positive_region")
        if hreg:
            print(
                f"  helical open-favored band: κ∈[{hreg['kappa_min']:.3f}, {hreg['kappa_max']:.3f}]  "
                f"({hreg['n']} points)"
            )
        # One-line best configuration for notebooks / CI logs
        print_best_anomaly_config(data)
        # per-IC detail at each κ
        for sl in data["slices"]:
            print(f"  κ={sl['kappa']:.3f} per-IC: {sl.get('per_ic')}")
        print(f"Wrote {plot_path}")
        print(f"Wrote {report}")
        return 0

    print("Packing density proxy (interpretive — not H₂O thermo)")
    print(f"  κ={args.kappa}  Δω={args.domega}  amps={args.n_amp}  ics={ics}")

    data = run_sweep(
        kappa=args.kappa,
        delta_omega=args.domega,
        amps=amps,
        ics=ics,
        nx=args.nx,
        nt=args.nt,
        frames=args.frames,
        n_sites=args.n_sites,
        seed=args.seed,
    )
    plot_path = OUTPUT_DIR / "packing_density_proxy.png"
    plot_results(data, plot_path)
    report = save_report("packing_density_proxy", data)

    a = data["analysis"]
    print("\n--- analysis ---")
    print(f"  pearson r(stab, open) = {a.get('pearson_stab_vs_open')}")
    print(f"  global slope stab vs open = {a.get('global_slope_stab_vs_open')}")
    print(f"  per-IC slopes: {a.get('per_ic')}")
    print_best_anomaly_config(data)
    print(f"Wrote {plot_path}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
