#!/usr/bin/env python3
"""
cardioid_golden_angle_probe.py
==============================
Resonance laboratory probe: golden-angle (and 9/π) stepping with cardioid
modulation r = 1 + cos(θ).

Mathematical layer only in metrics — the cusp (θ ≈ π, r → 0) is a geometric
high-sensitivity zone used as a measurable proxy for burst-threshold /
directional-alignment structure. Interpretive framing lives in
notes/CARDIOID_RESONANCE.md.

Builds on golden_angle_twist_probe.py and vortex_369_clock.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    E,
    GOLDEN_ANGLE_DEG,
    OUTPUT_DIR,
    PHI,
    PI,
    R_RESIDUAL,
    W_G_LOCK,
    law_of_cosines_angle,
    save_report,
)

# ---------------------------------------------------------------------------
# Stepping angles
# ---------------------------------------------------------------------------
# Golden angle: θ_g = 2π (1 − 1/φ) = 2π / φ²  (phyllotaxis / low-discrepancy)
GOLDEN_ANGLE_RAD = float(np.radians(GOLDEN_ANGLE_DEG))  # ≈ 2.399963 rad
NINE_OVER_PI_RAD = 9.0 / PI  # ≈ 2.8648 rad ≈ 164.1°
NINE_OVER_PI_DEG = float(np.degrees(NINE_OVER_PI_RAD))
W_G = 350.0 / PI  # ≈ 111.408 — magic-island / accumulation scale

# Cusp neighbourhood on the unit circle (θ ≈ π for the cardioid r=1+cos θ)
CUSP_HALF_WIDTH_RAD = 0.25  # ±0.25 rad ≈ ±14.3° around π
DEFAULT_N = 512
ALIGN_KERNEL_WIDTH = 0.20  # rad — Gaussian width for local_support

# ---------------------------------------------------------------------------
# Metric formulas (mathematical layer — explicit, reproducible)
# ---------------------------------------------------------------------------
# Stepping:
#   θ_k = (k · θ_step) mod 2π
#   golden: θ_step = θ_g = 2π/φ²
#   optional: θ_step = 9/π
#
# Cardioid envelope:
#   r(θ) = 1 + cos(θ)     →  cusp at θ=π, r=0; far lobe θ=0, r=2
#
# Cusp window indicator (angular distance on S¹):
#   near_cusp_k  ⇔  |((θ_k − π + π) mod 2π) − π|  ≤  w
#   with default w = CUSP_HALF_WIDTH_RAD = 0.25
#
# cusp_fraction:
#   f_cusp = (1/N) Σ_k 1_near(k)
#
# expected_uniform_fraction (equidistribution baseline):
#   f_exp = 2w / (2π) = w/π
#
# cusp_density_ratio ρ:
#   ρ = f_cusp / f_exp
#   → ≈ 1 for irrational rotation (no angular pile-up)
#
# align_support (φ-e-π alignment support):
#   targets α_φ, α_e, α_π = law-of-cosines angles (rad) of sides φ, e, π
#   For each target α:
#     d_k = circular_dist(θ_k, α)
#     w_k = exp(−½ (d_k / σ)²),  σ = ALIGN_KERNEL_WIDTH
#     S(α) = (Σ w_k r_k) / (Σ w_k)  /  2     ∈ [0, 1]  (r∈[0,2] for cardioid)
#   align_support = mean{ S(α_φ), S(α_e), S(α_π) }
#   Note: triangle angles sit on the cardioid *body* (elevated r vs unit circle),
#   not at the cusp — radial *weighting*, not cusp pile-up.
#
# packing gap_cv:
#   sort θ on S¹; gaps g_i including wrap-around;  gap_cv = std(g) / mean(g)
#
# cusp_coherence (scale sweep composite):
#   packing_uniformity = 1 / (1 + gap_cv)
#   cusp_coherence = ρ · packing_uniformity · (0.5 + 0.5 · frac_369_cusp)
#   higher = denser-than-uniform cusp ∧ more even packing ∧ more 3-6-9 in window
#
# radial_collapse (reported in cusp_resonance_probe, same cusp window):
#   radial_collapse = mean(r | bulk) / mean(r | cusp)
# ---------------------------------------------------------------------------


def digital_root(n: int) -> int:
    """Rodin-style digital root (0 → 9)."""
    if n == 0:
        return 9
    r = n % 9
    return 9 if r == 0 else r


def step_angles(n: int, step_rad: float, theta0: float = 0.0) -> np.ndarray:
    """θ_k = (θ0 + k · step) mod 2π."""
    k = np.arange(n, dtype=float)
    return (theta0 + k * step_rad) % (2.0 * PI)


def cardioid_radii(theta: np.ndarray) -> np.ndarray:
    """Classic cardioid envelope: r(θ) = 1 + cos(θ). Cusp at θ = π, r = 0."""
    return 1.0 + np.cos(theta)


def polar_to_xy(theta: np.ndarray, r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return r * np.cos(theta), r * np.sin(theta)


def cusp_mask(theta: np.ndarray, half_width: float = CUSP_HALF_WIDTH_RAD) -> np.ndarray:
    """Points whose angular distance to π is ≤ half_width."""
    d = np.abs(((theta - PI + PI) % (2.0 * PI)) - PI)
    return d <= half_width


def vortex_labels(indices: np.ndarray) -> np.ndarray:
    """Vortex 3-6-9 digital roots of step indices (1-based for display parity)."""
    return np.array([digital_root(int(i) + 1) for i in indices], dtype=int)


def label_distribution(labels: np.ndarray) -> dict[str, float]:
    total = max(len(labels), 1)
    counts = {str(d): int(np.sum(labels == d)) for d in range(1, 10)}
    frac_369 = float(np.mean(np.isin(labels, [3, 6, 9]))) if len(labels) else 0.0
    dominant = max(counts, key=counts.get) if labels.size else "none"
    return {
        "counts": counts,
        "fraction_369": frac_369,
        "dominant_digit": dominant,
        "n": int(len(labels)),
    }


def phi_e_pi_alignment_score(theta: np.ndarray, r: np.ndarray) -> dict:
    """
    align_support — geometric diagnostic for φ-e-π triangle angles on the cloud.

    Formula (per target angle α ∈ {α_φ, α_e, α_π}):
        d_k = circular_dist(θ_k, α)
        w_k = exp(−½ (d_k / σ)²),  σ = ALIGN_KERNEL_WIDTH
        S(α) = (Σ_k w_k r_k) / (Σ_k w_k) / 2     # r/2 maps cardioid [0,2] → [0,1]
        align_support = (S(α_φ) + S(α_e) + S(α_π)) / 3

    Unit circle (r≡1) ⇒ align_support = 0.5 exactly (up to sampling noise).
    Cardioid elevates S at body angles where r = 1+cos θ > 1.

    Purely geometric — not a claim that R is forced by the cardioid.
    """
    phi_ang = np.radians(law_of_cosines_angle(PHI, E, PI))  # opposite φ
    e_ang = np.radians(law_of_cosines_angle(E, PHI, PI))
    pi_ang = np.radians(law_of_cosines_angle(PI, PHI, E))
    targets = {
        "phi_angle_rad": float(phi_ang),
        "e_angle_rad": float(e_ang),
        "pi_angle_rad": float(pi_ang),
    }

    def local_support(target: float, width: float = ALIGN_KERNEL_WIDTH) -> float:
        # circular_dist on S¹
        d = np.abs(((theta - target + PI) % (2.0 * PI)) - PI)
        w = np.exp(-0.5 * (d / width) ** 2)
        if w.sum() < 1e-12:
            return 0.0
        return float(np.average(r, weights=w) / 2.0)  # normalize r∈[0,2] → [0,1]

    supports = {k: local_support(v) for k, v in targets.items()}
    mean_support = float(np.mean(list(supports.values())))

    near = cusp_mask(theta)
    global_mean_dev = float(np.mean(np.abs(r - 1.0)))
    cusp_mean_r = float(np.mean(r[near])) if near.any() else float("nan")
    residual_proxy = abs(mean_support - R_RESIDUAL)

    return {
        "formula": (
            "align_support = mean_α [ (Σ w_k r_k)/(Σ w_k)/2 ], "
            f"w_k=exp(−½(d_k/σ)²), σ={ALIGN_KERNEL_WIDTH}"
        ),
        "triangle_angle_supports": supports,
        "mean_alignment_support": mean_support,
        "cusp_mean_radius": cusp_mean_r,
        "global_mean_abs_r_minus_1": global_mean_dev,
        "residual_R": float(R_RESIDUAL),
        "delta_support_vs_R": float(mean_support - R_RESIDUAL),
        "residual_proxy_abs": float(residual_proxy),
        "note": (
            "Alignment support is a geometric diagnostic on the modulated point cloud; "
            "it does not prove R emerges from the cardioid."
        ),
    }


def packing_efficiency(theta: np.ndarray) -> dict:
    """Angular gap statistics — golden stepping minimizes overlap (phyllotaxis)."""
    sorted_t = np.sort(theta)
    gaps = np.diff(sorted_t)
    wrap = (sorted_t[0] + 2.0 * PI) - sorted_t[-1]
    gaps = np.concatenate([gaps, [wrap]])
    return {
        "mean_gap_rad": float(np.mean(gaps)),
        "std_gap_rad": float(np.std(gaps)),
        "min_gap_rad": float(np.min(gaps)),
        "max_gap_rad": float(np.max(gaps)),
        "gap_cv": float(np.std(gaps) / (np.mean(gaps) + 1e-12)),
    }


def analyze_system(
    n: int,
    step_rad: float,
    step_name: str,
    *,
    modulate: bool = True,
    cusp_half_width: float = CUSP_HALF_WIDTH_RAD,
) -> dict:
    theta = step_angles(n, step_rad)
    r = cardioid_radii(theta) if modulate else np.ones_like(theta)
    x, y = polar_to_xy(theta, r)
    near = cusp_mask(theta, cusp_half_width)
    labels = vortex_labels(np.arange(n))
    cusp_labels = labels[near]
    cusp_dist = label_distribution(cusp_labels)
    all_dist = label_distribution(labels)
    alignment = phi_e_pi_alignment_score(theta, r)
    packing = packing_efficiency(theta)

    # f_cusp = (# near cusp) / N;  f_exp = 2w/(2π) = w/π;  ρ = f_cusp / f_exp
    cusp_frac = float(np.mean(near))
    expected_frac = (2.0 * cusp_half_width) / (2.0 * PI)
    density_ratio = cusp_frac / expected_frac if expected_frac > 0 else float("nan")

    # radial_collapse = mean(r|bulk) / mean(r|cusp)  (≥1 when cusp collapses)
    bulk = ~near
    mean_r_cusp = float(np.mean(r[near])) if near.any() else float("nan")
    mean_r_bulk = float(np.mean(r[bulk])) if bulk.any() else float("nan")
    radial_collapse = (
        mean_r_bulk / (mean_r_cusp + 1e-12)
        if mean_r_cusp == mean_r_cusp
        else float("nan")
    )

    return {
        "step_name": step_name,
        "step_rad": float(step_rad),
        "step_deg": float(np.degrees(step_rad)),
        "n": n,
        "modulated": modulate,
        "cusp_half_width_rad": cusp_half_width,
        "points_near_cusp": int(np.sum(near)),
        "cusp_fraction": cusp_frac,
        "expected_uniform_fraction": float(expected_frac),
        "cusp_density_ratio": float(density_ratio),
        "cusp_density_ratio_formula": "ρ = f_cusp / (w/π),  f_cusp = (#|θ−π|≤w)/N",
        "mean_r_cusp": mean_r_cusp,
        "mean_r_bulk": mean_r_bulk,
        "radial_collapse": float(radial_collapse),
        "radial_collapse_formula": "mean(r|bulk) / mean(r|cusp)",
        "cusp_vortex_labels": cusp_dist,
        "all_vortex_labels": all_dist,
        "dominant_vortex_digits_cusp": cusp_dist["dominant_digit"],
        "phi_e_pi_alignment": alignment,
        "packing": packing,
        "mean_radius": float(np.mean(r)),
        "std_radius": float(np.std(r)),
        "min_radius": float(np.min(r)),
        "theta": theta,
        "r": r,
        "x": x,
        "y": y,
        "near_cusp": near,
    }


def scale_sweep_coherence(
    step_rad: float,
    *,
    base_n: float = W_G,
    factors: list[float] | None = None,
    cusp_half_width: float = CUSP_HALF_WIDTH_RAD,
) -> list[dict]:
    """
    Cusp coherence at N near multiples/fractions of 350/π.

    Explicit formula:
        packing_uniformity = 1 / (1 + gap_cv)
        cusp_coherence = ρ · packing_uniformity · (0.5 + 0.5 · frac_369_cusp)

    where ρ = cusp_density_ratio, frac_369_cusp = fraction of digital roots
    in {3,6,9} among cusp-window indices.
    Higher = denser-than-uniform cusp ∧ even packing ∧ stronger 3-6-9 in window.
    """
    if factors is None:
        factors = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, PHI, PI]
    rows = []
    for f in factors:
        n = max(8, int(round(base_n * f)))
        sys_m = analyze_system(n, step_rad, "scale", modulate=True, cusp_half_width=cusp_half_width)
        packing_uniformity = 1.0 / (1.0 + sys_m["packing"]["gap_cv"])
        # cusp_coherence = ρ · 1/(1+gap_cv) · (0.5 + 0.5·frac_369)
        coherence = (
            sys_m["cusp_density_ratio"]
            * packing_uniformity
            * (0.5 + 0.5 * sys_m["cusp_vortex_labels"]["fraction_369"])
        )
        rows.append({
            "factor": float(f),
            "n": n,
            "n_over_W_g": float(n / base_n),
            "cusp_density_ratio": sys_m["cusp_density_ratio"],
            "points_near_cusp": sys_m["points_near_cusp"],
            "fraction_369_cusp": sys_m["cusp_vortex_labels"]["fraction_369"],
            "gap_cv": sys_m["packing"]["gap_cv"],
            "packing_uniformity": float(packing_uniformity),
            "alignment_support": sys_m["phi_e_pi_alignment"]["mean_alignment_support"],
            "cusp_coherence": float(coherence),
            "cusp_coherence_formula": "ρ · 1/(1+gap_cv) · (0.5 + 0.5·frac_369_cusp)",
        })
    return rows


def plot_cardioid_comparison(
    systems: list[dict],
    path: Path,
    *,
    scale_rows: list[dict] | None = None,
) -> None:
    """Heart-shaped clouds, cusp highlight, stats table, optional scale curve."""
    n_sys = len(systems)
    ncols = 3 if n_sys >= 3 else max(n_sys, 2)
    fig = plt.figure(figsize=(4.2 * ncols, 9.0))
    gs = fig.add_gridspec(2, ncols, height_ratios=[1.15, 0.95], hspace=0.32, wspace=0.28)

    # Continuous cardioid outline for reference
    th_ref = np.linspace(0, 2 * PI, 400)
    r_ref = cardioid_radii(th_ref)
    xref, yref = polar_to_xy(th_ref, r_ref)

    for i, sys in enumerate(systems[:ncols]):
        ax = fig.add_subplot(gs[0, i])
        ax.plot(xref, yref, color="#888", lw=1.0, alpha=0.5, zorder=1)
        ax.scatter(
            sys["x"][~sys["near_cusp"]],
            sys["y"][~sys["near_cusp"]],
            s=8,
            c="#2a9d8f",
            alpha=0.55,
            edgecolors="none",
            zorder=2,
            label="bulk",
        )
        ax.scatter(
            sys["x"][sys["near_cusp"]],
            sys["y"][sys["near_cusp"]],
            s=22,
            c="#e63946",
            alpha=0.9,
            edgecolors="#222",
            linewidths=0.3,
            zorder=3,
            label="cusp",
        )
        # Cusp marker at origin (cardioid cusp)
        ax.plot(0, 0, "k*", ms=10, zorder=4)
        ax.set_aspect("equal")
        ax.set_xlim(-0.3, 2.2)
        ax.set_ylim(-1.6, 1.6)
        mod = "cardioid" if sys["modulated"] else "unit r"
        ax.set_title(
            f"{sys['step_name']}\n"
            f"{mod} · N={sys['n']} · cusp n={sys['points_near_cusp']}",
            fontsize=9,
        )
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(alpha=0.25)
        ax.set_xlabel("x = r cos θ")
        ax.set_ylabel("y = r sin θ")

    # Bottom-left: statistics table
    ax_t = fig.add_subplot(gs[1, 0])
    ax_t.axis("off")
    rows_txt = []
    for sys in systems:
        rows_txt.append(
            f"{sys['step_name'][:18]:18s}  "
            f"cusp={sys['points_near_cusp']:3d}  "
            f"ρ={sys['cusp_density_ratio']:.2f}  "
            f"369={sys['cusp_vortex_labels']['fraction_369']:.2f}  "
            f"dom={sys['dominant_vortex_digits_cusp']}  "
            f"align={sys['phi_e_pi_alignment']['mean_alignment_support']:.3f}"
        )
    table_body = "\n".join(rows_txt)
    ax_t.text(
        0.02, 0.95,
        "Cusp statistics\n"
        f"(window ±{CUSP_HALF_WIDTH_RAD:.2f} rad around θ=π)\n\n"
        f"{'system':18s}  cusp   ρ_cusp  frac369  dom  align\n"
        + "-" * 62 + "\n"
        + table_body
        + f"\n\nR = {R_RESIDUAL:.6f}  ·  W_g = 350/π ≈ {W_G:.3f}\n"
        f"golden step = {GOLDEN_ANGLE_DEG:.4f}°  ·  9/π ≈ {NINE_OVER_PI_DEG:.2f}°",
        transform=ax_t.transAxes,
        fontsize=8,
        family="monospace",
        va="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8f5f0", edgecolor="#ccc"),
    )
    ax_t.set_title("Metrics table", fontsize=10, loc="left")

    # Bottom-middle: angular density near cusp (polar-style histogram comparison)
    ax_h = fig.add_subplot(gs[1, 1])
    bins = np.linspace(0, 2 * PI, 37)
    for sys, color in zip(systems, ["#264653", "#2a9d8f", "#e9c46a", "#e76f51"]):
        ax_h.hist(
            sys["theta"],
            bins=bins,
            alpha=0.45,
            color=color,
            label=sys["step_name"][:20],
            density=True,
        )
    ax_h.axvline(PI, color="#e63946", ls="--", lw=1.2, label="cusp θ=π")
    ax_h.set_xlabel("θ (rad)")
    ax_h.set_ylabel("density")
    ax_h.set_title("Angular density", fontsize=10)
    ax_h.legend(fontsize=7)
    ax_h.grid(alpha=0.3)

    # Bottom-right: 350/π scale coherence (if provided)
    ax_s = fig.add_subplot(gs[1, 2] if ncols >= 3 else gs[1, 1])
    if scale_rows:
        xs = [r["n_over_W_g"] for r in scale_rows]
        ys = [r["cusp_coherence"] for r in scale_rows]
        ax_s.plot(xs, ys, "o-", color="#6a4c93", lw=1.5, ms=5)
        ax_s.axvline(1.0, color="#c9a227", ls="--", label="N = 350/π")
        # Mark φ and π factors if present
        for r in scale_rows:
            if abs(r["factor"] - PHI) < 0.02:
                ax_s.axvline(r["n_over_W_g"], color="#2a9d8f", ls=":", alpha=0.7, label="×φ")
            if abs(r["factor"] - PI) < 0.02:
                ax_s.axvline(r["n_over_W_g"], color="#e76f51", ls=":", alpha=0.7, label="×π")
        ax_s.set_xlabel("N / (350/π)")
        ax_s.set_ylabel("cusp coherence")
        ax_s.set_title("Scale sweep @ 350/π", fontsize=10)
        ax_s.legend(fontsize=7)
        ax_s.grid(alpha=0.3)
    else:
        ax_s.axis("off")
        ax_s.text(0.5, 0.5, "No scale sweep", ha="center", va="center")

    fig.suptitle(
        "Cardioid × golden-angle resonance probe\n"
        "r = 1 + cos(θ)  ·  cusp = burst-threshold geometric proxy",
        fontsize=12,
        y=1.01,
    )
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_density_heatmap(sys: dict, path: Path) -> None:
    """Focused cusp density: hexbin + angular zoom for one system."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    ax = axes[0]
    hb = ax.hexbin(sys["x"], sys["y"], gridsize=40, cmap="magma", mincnt=1)
    plt.colorbar(hb, ax=ax, fraction=0.046, label="count")
    ax.plot(0, 0, "c*", ms=12)
    ax.set_aspect("equal")
    ax.set_title(f"Density — {sys['step_name']}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    ax2 = axes[1]
    near = sys["near_cusp"]
    th = sys["theta"]
    r = sys["r"]
    d = ((th - PI + PI) % (2 * PI)) - PI
    ax2.scatter(d[~near], r[~near], s=6, c="#457b9d", alpha=0.4, label="bulk")
    ax2.scatter(d[near], r[near], s=18, c="#e63946", alpha=0.85, label="cusp window")
    ax2.axvline(0, color="#333", ls="--", lw=0.8)
    ax2.set_xlabel("θ − π (rad)")
    ax2.set_ylabel("r = 1 + cos θ")
    ax2.set_title("Cusp zoom (angular)")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)

    fig.suptitle("Cardioid cusp density", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_three_way_star(
    golden_unit: dict,
    golden_mod: dict,
    nine_mod: dict,
    path: Path,
) -> None:
    """
    High-impact star figure: golden (unit r) | golden+cardioid | 9/π+cardioid
    plus a focused cusp density panel for golden+cardioid.
    """
    systems = [golden_unit, golden_mod, nine_mod]
    titles = [
        "Golden (unit r)",
        "Golden + cardioid",
        "9/π + cardioid",
    ]
    th_ref = np.linspace(0, 2 * PI, 400)
    r_ref = cardioid_radii(th_ref)
    xref, yref = polar_to_xy(th_ref, r_ref)

    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1.0], hspace=0.28, wspace=0.25)

    for i, (sys, title) in enumerate(zip(systems, titles)):
        ax = fig.add_subplot(gs[0, i])
        if sys["modulated"]:
            ax.plot(xref, yref, color="#888", lw=1.0, alpha=0.55, zorder=1)
        else:
            # unit circle reference
            ax.plot(np.cos(th_ref), np.sin(th_ref), color="#888", lw=1.0, alpha=0.55, zorder=1)
        ax.scatter(
            sys["x"][~sys["near_cusp"]], sys["y"][~sys["near_cusp"]],
            s=10, c="#2a9d8f", alpha=0.55, edgecolors="none", zorder=2, label="bulk",
        )
        ax.scatter(
            sys["x"][sys["near_cusp"]], sys["y"][sys["near_cusp"]],
            s=28, c="#e63946", alpha=0.92, edgecolors="#222", linewidths=0.35,
            zorder=3, label="cusp",
        )
        ax.plot(0, 0, "k*", ms=11, zorder=4)
        ax.set_aspect("equal")
        lim = 2.25 if sys["modulated"] else 1.35
        ax.set_xlim(-lim * 0.15 if sys["modulated"] else -lim, lim)
        ax.set_ylim(-lim * 0.75, lim * 0.75)
        if not sys["modulated"]:
            ax.set_xlim(-lim, lim)
            ax.set_ylim(-lim, lim)
        align = sys["phi_e_pi_alignment"]["mean_alignment_support"]
        collapse = sys.get("radial_collapse", float("nan"))
        ax.set_title(
            f"{title}\n"
            f"N={sys['n']}  cusp={sys['points_near_cusp']}  "
            f"ρ={sys['cusp_density_ratio']:.3f}\n"
            f"align={align:.3f}  collapse={collapse:.2f}",
            fontsize=9,
        )
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(alpha=0.25)
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    # Bottom-left: cusp density heatmap (golden+cardioid) + r-distribution inset
    ax = fig.add_subplot(gs[1, 0])
    hb = ax.hexbin(golden_mod["x"], golden_mod["y"], gridsize=45, cmap="magma", mincnt=1)
    plt.colorbar(hb, ax=ax, fraction=0.046, label="count")
    ax.plot(0, 0, "c*", ms=12)
    ax.set_aspect("equal")
    ax.set_title("Cusp density — golden+cardioid", fontsize=10)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    # Inset: bulk vs cusp r histogram (makes radial_collapse visceral)
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    ax_in = inset_axes(ax, width="42%", height="38%", loc="upper right", borderpad=0.6)
    r_bulk = golden_mod["r"][~golden_mod["near_cusp"]]
    r_cusp = golden_mod["r"][golden_mod["near_cusp"]]
    bins = np.linspace(0, 2.05, 28)
    ax_in.hist(r_bulk, bins=bins, color="#2a9d8f", alpha=0.7, density=True, label="bulk")
    ax_in.hist(r_cusp, bins=bins, color="#e63946", alpha=0.75, density=True, label="cusp")
    ax_in.set_xlabel("r", fontsize=6)
    ax_in.set_ylabel("dens.", fontsize=6)
    ax_in.tick_params(labelsize=5)
    ax_in.set_title("r dist.", fontsize=6, pad=2)
    ax_in.legend(fontsize=5, loc="upper left", framealpha=0.85)
    ax_in.set_xlim(0, 2.05)

    # Bottom-middle: metrics bar chart (collapse displayed as log10 for scale)
    ax = fig.add_subplot(gs[1, 1])
    labels = ["unit r", "gold+card", "9/π+card"]
    aligns = [s["phi_e_pi_alignment"]["mean_alignment_support"] for s in systems]
    collapses = [float(s.get("radial_collapse", 1.0)) for s in systems]
    # log10(collapse) keeps full-cardioid cusp (r→0) readable beside align∈[0,1]
    log_coll = [np.log10(max(c, 1.0)) for c in collapses]
    x = np.arange(3)
    w = 0.35
    ax.bar(x - w / 2, aligns, w, color="#2a9d8f", label="align_support")
    ax.bar(x + w / 2, log_coll, w, color="#e63946", label="log₁₀(collapse)")
    ax.axhline(0.5, color="#457b9d", ls="--", lw=0.9, label="unit align=0.5")
    for i, c in enumerate(collapses):
        ax.text(i + w / 2, log_coll[i] + 0.05, f"{c:.1f}", ha="center", fontsize=7, color="#e63946")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("score")
    ax.set_title("align_support vs radial_collapse", fontsize=10)
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3, axis="y")

    # Bottom-right: formula card
    ax = fig.add_subplot(gs[1, 2])
    ax.axis("off")
    ax.text(
        0.02, 0.98,
        "Metric formulas (math layer)\n"
        "─────────────────────────────\n"
        "θ_k = k·θ_step  (mod 2π)\n"
        "  golden: θ_g = 2π/φ²\n"
        "  alt:    9/π\n"
        "r(θ) = 1 + cos(θ)   cusp @ θ=π\n"
        "\n"
        "ρ = f_cusp / (w/π)\n"
        "  f_cusp = (# |θ−π|≤w) / N\n"
        "\n"
        "align_support =\n"
        "  mean_α [(Σ w_k r_k)/(Σ w_k)/2]\n"
        "  w_k = exp(−½(d_k/σ)²)\n"
        "\n"
        "radial_collapse =\n"
        "  mean(r|bulk) / mean(r|cusp)\n"
        "\n"
        "cusp_coherence =\n"
        "  ρ · 1/(1+gap_cv) · (½+½ frac_369)\n"
        f"\nR = {R_RESIDUAL:.6f}\n"
        f"W_g = 350/π ≈ {W_G:.3f}\n"
        f"w = {CUSP_HALF_WIDTH_RAD} rad",
        transform=ax.transAxes,
        fontsize=8.5,
        family="monospace",
        va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f5f0", edgecolor="#bbb"),
    )

    fig.suptitle(
        "Cardioid resonance — three-way comparison\n"
        "Uniform angular sampling (golden / 9/π) × radial cardioid envelope",
        fontsize=12,
        y=1.01,
    )
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _strip_arrays(sys: dict) -> dict:
    """JSON-safe copy without large ndarrays."""
    skip = {"theta", "r", "x", "y", "near_cusp"}
    return {k: v for k, v in sys.items() if k not in skip}


def main() -> int:
    parser = argparse.ArgumentParser(description="Cardioid × golden-angle resonance probe")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="Number of steps")
    parser.add_argument(
        "--cusp-width",
        type=float,
        default=CUSP_HALF_WIDTH_RAD,
        help="Half-width (rad) of cusp window around π",
    )
    parser.add_argument("--no-scale-sweep", action="store_true")
    args = parser.parse_args()

    n = args.n
    cw = args.cusp_width

    # Core systems
    golden_mod = analyze_system(n, GOLDEN_ANGLE_RAD, "golden+cardioid", modulate=True, cusp_half_width=cw)
    golden_raw = analyze_system(n, GOLDEN_ANGLE_RAD, "golden (unit r)", modulate=False, cusp_half_width=cw)
    nine_mod = analyze_system(n, NINE_OVER_PI_RAD, "9/π+cardioid", modulate=True, cusp_half_width=cw)
    # Also uniform-ish control for comparison (rational step)
    control_mod = analyze_system(n, 2.0 * PI / 17.0, "2π/17+cardioid", modulate=True, cusp_half_width=cw)

    scale_rows = None if args.no_scale_sweep else scale_sweep_coherence(
        GOLDEN_ANGLE_RAD, base_n=W_G, cusp_half_width=cw
    )

    plot_path = OUTPUT_DIR / "cardioid_golden_angle_probe.png"
    plot_cardioid_comparison(
        [golden_raw, golden_mod, nine_mod],
        plot_path,
        scale_rows=scale_rows,
    )
    density_path = OUTPUT_DIR / "cardioid_cusp_density.png"
    plot_density_heatmap(golden_mod, density_path)
    star_path = OUTPUT_DIR / "cardioid_three_way_star.png"
    plot_three_way_star(golden_raw, golden_mod, nine_mod, star_path)

    # Comparison metrics: modulated golden vs unmodulated
    comparison = {
        "cusp_points_delta": golden_mod["points_near_cusp"] - golden_raw["points_near_cusp"],
        "density_ratio_golden_mod": golden_mod["cusp_density_ratio"],
        "density_ratio_golden_raw": golden_raw["cusp_density_ratio"],
        "alignment_mod": golden_mod["phi_e_pi_alignment"]["mean_alignment_support"],
        "alignment_raw": golden_raw["phi_e_pi_alignment"]["mean_alignment_support"],
        "alignment_nine_mod": nine_mod["phi_e_pi_alignment"]["mean_alignment_support"],
        "gap_cv_golden": golden_mod["packing"]["gap_cv"],
        "gap_cv_nine": nine_mod["packing"]["gap_cv"],
        "gap_cv_control": control_mod["packing"]["gap_cv"],
        "note": (
            "Golden stepping keeps gap_cv low (efficient packing). Cardioid modulates radius only; "
            "angular density ratios stay near-uniform for irrational rotations — cusp sensitivity "
            "appears in r→0 and local label/alignment scores."
        ),
    }

    best_scale = None
    if scale_rows:
        best_scale = max(scale_rows, key=lambda r: r["cusp_coherence"])

    payload = {
        "constants": {
            "golden_angle_deg": GOLDEN_ANGLE_DEG,
            "golden_angle_rad": GOLDEN_ANGLE_RAD,
            "nine_over_pi_rad": NINE_OVER_PI_RAD,
            "nine_over_pi_deg": NINE_OVER_PI_DEG,
            "W_g": float(W_G),
            "W_G_LOCK": float(W_G_LOCK),
            "R_residual": float(R_RESIDUAL),
            "cusp_at": "θ=π, r=0 for r=1+cos(θ)",
        },
        "systems": {
            "golden_cardioid": _strip_arrays(golden_mod),
            "golden_unit": _strip_arrays(golden_raw),
            "nine_over_pi_cardioid": _strip_arrays(nine_mod),
            "control_2pi_17_cardioid": _strip_arrays(control_mod),
        },
        "comparison": comparison,
        "scale_sweep_350_over_pi": scale_rows,
        "best_scale": best_scale,
        "plots": {
            "main": str(plot_path),
            "density": str(density_path),
            "three_way_star": str(star_path),
        },
        "metric_formulas": {
            "stepping": "θ_k = (k · θ_step) mod 2π;  θ_g = 2π/φ²;  alt = 9/π",
            "cardioid": "r(θ) = 1 + cos(θ)",
            "cusp_density_ratio": "ρ = f_cusp / (w/π),  f_cusp = (#|θ−π|≤w)/N",
            "align_support": (
                "mean_α[(Σ w_k r_k)/(Σ w_k)/2], w_k=exp(−½(d_k/σ)²), "
                f"σ={ALIGN_KERNEL_WIDTH}"
            ),
            "radial_collapse": "mean(r|bulk) / mean(r|cusp)",
            "cusp_coherence": "ρ · 1/(1+gap_cv) · (0.5 + 0.5·frac_369_cusp)",
            "burst_fraction": "see cusp_resonance_probe: mean(holonomy > θ_crit)",
        },
        "interpretation": (
            "Mathematical: cardioid is a resonance envelope on irrational (golden) or 9/π "
            "stepping; cusp has infinite curvature and maps to a high-sensitivity locus. "
            "Observational: cusp window metrics and 350/π scale coherence are diagnostics. "
            "Interpretive claims (frequency alignment, efficient exit) are optional and "
            "documented separately in notes/CARDIOID_RESONANCE.md."
        ),
    }
    report_path = save_report("cardioid_golden_angle_probe", payload)

    print("=== Cardioid × Golden-Angle Resonance Probe ===")
    print(f"Golden angle: {GOLDEN_ANGLE_DEG:.4f}°  ·  9/π: {NINE_OVER_PI_DEG:.2f}°  ·  W_g={W_G:.4f}")
    print(f"N={n}  cusp window ±{cw:.3f} rad around π")
    print(
        f"Golden+cardioid — cusp points: {golden_mod['points_near_cusp']}  "
        f"ρ={golden_mod['cusp_density_ratio']:.3f}  "
        f"369={golden_mod['cusp_vortex_labels']['fraction_369']:.3f}  "
        f"dom={golden_mod['dominant_vortex_digits_cusp']}  "
        f"align={golden_mod['phi_e_pi_alignment']['mean_alignment_support']:.4f}  "
        f"collapse={golden_mod['radial_collapse']:.3f}"
    )
    print(
        f"Golden unit r  — cusp points: {golden_raw['points_near_cusp']}  "
        f"align={golden_raw['phi_e_pi_alignment']['mean_alignment_support']:.4f}  "
        f"collapse={golden_raw['radial_collapse']:.3f}"
    )
    print(
        f"9/π+cardioid   — cusp points: {nine_mod['points_near_cusp']}  "
        f"gap_cv={nine_mod['packing']['gap_cv']:.4f}  "
        f"(golden gap_cv={golden_mod['packing']['gap_cv']:.4f})"
    )
    if best_scale:
        print(
            f"Best 350/π scale: N={best_scale['n']}  "
            f"(×{best_scale['factor']:.3f})  coherence={best_scale['cusp_coherence']:.4f}"
        )
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    print(f"Density:{density_path}")
    print(f"Star:   {star_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
