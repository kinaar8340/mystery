#!/usr/bin/env python3
"""PDE relaxation seeded with meta-optimizer constants; FFT + correlation analysis.

Optional cardioid coupling (resonance-lab layer):
    effective dynamics multiply the non-diffusive drive by
    (1 + cardioid_amp · cos(θ)), so the cusp θ≈π is a high-sensitivity locus
    for burst / gauge terms. Toggle with --cardioid-amp or CARDIOID_AMP env.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, R_RESIDUAL, save_report

META_JSON = OUTPUT_DIR / "meta_optimize_phi_probe_20260628_022307.json"
TRANSCENDENTALS = {"phi": PHI, "e": E, "pi": PI, "one": 1.0}
CUSP_W = 0.25  # rad — shared cusp half-width with geometric probes


def load_meta_seeds() -> dict:
    if META_JSON.is_file():
        data = json.loads(META_JSON.read_text())
        mo = data.get("meta_optimize", {})
        return {
            "kappa": mo.get("best_kappa", 0.85),
            "wg_base": 351.5,
            "w_g": mo.get("best_w_g", 350 / PI),
            "braiding": mo.get("best_braiding", 0.754),
        }
    return {"kappa": 0.85, "wg_base": 351.5, "w_g": 350 / PI, "braiding": 0.754}


def _grid_coords(nx: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lin = np.linspace(0, 2 * PI, nx, endpoint=False)
    return np.meshgrid(lin, lin, lin, indexing="ij")


def build_ic(name: str, nx: int, seed: int = 42, kappa: float = 0.85) -> np.ndarray:
    """
    Initial conditions for PDE cardioid tests.

    Names: uniform | hopfion | helical | combined
    (helical = two_gyro_helix from pde_structured_ic_probe)
    """
    t_crit = PI * (1.0 + kappa)
    if name in ("uniform", "random"):
        rng = np.random.default_rng(seed)
        return rng.uniform(0.1, 2.0, (nx, nx, nx))
    if name in ("hopfion", "hopfion_blob"):
        # Localized blob peaked at θ=π (cusp locus) so |θ−π|≤w is populated
        x, y, z = _grid_coords(nx)
        cx = cy = cz = PI
        r2 = (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2
        blob = PI * np.exp(-r2 / (2 * 0.45**2))  # core → π
        return np.clip(0.15 + blob, 0.05, t_crit - 0.05)
    if name in ("helical", "helix", "two_gyro_helix"):
        # Counter-rotating helices spanning through π so cusp window is populated
        x, y, z = _grid_coords(nx)
        k = 2.0
        amp = 1.8
        cw = amp * np.sin(k * x + 0.5 * z)
        ccw = amp * np.sin(k * x - 0.5 * z)
        return np.clip(PI * 0.55 + cw + 0.6 * ccw, 0.1, t_crit - 0.1)
    if name == "combined":
        return np.clip(
            build_ic("hopfion", nx, seed, kappa) + 0.4 * build_ic("helical", nx, seed, kappa),
            0.1,
            t_crit - 0.05,
        )
    raise ValueError(f"Unknown IC '{name}'; choose uniform|hopfion|helical|combined")


def digital_root_bin(values: np.ndarray) -> dict:
    """
    Vortex 3-6-9 coherence on a scalar field: map sites to digital roots of
    floor(10·θ) (tens-of-units style) and report frac in {3,6,9}.
    """
    # Quantize to positive ints without forcing 369 structure
    q = np.maximum(1, np.floor(10.0 * values).astype(int))
    # digital root: 1 + (n-1) % 9
    dr = 1 + (q - 1) % 9
    total = dr.size
    counts = {str(d): int(np.sum(dr == d)) for d in range(1, 10)}
    frac_369 = float(np.mean(np.isin(dr, [3, 6, 9])))
    return {
        "counts": counts,
        "fraction_369": frac_369,
        "n": int(total),
        "formula": "dr = 1 + (floor(10·θ)-1) mod 9;  frac_369 = mean(dr ∈ {3,6,9})",
    }


def simulate_pde(
    nx: int = 20,
    nt: int = 3000,
    dt: float = 0.001,
    D: float = 0.05,
    kappa: float = 0.85,
    delta_omega: float = 0.002,
    theta_crit: float | None = None,
    seed: int = 42,
    normalize_to_lambda_t: float | None = None,
    cardioid_amp: float = 0.0,
    initial_theta: np.ndarray | None = None,
) -> np.ndarray:
    """
    Gauged twist PDE relaxation on a cubic lattice.

    Base update (per step):
        ∂t θ = D ∇²θ + cot_term + δω − κ⟨θ⟩ + burst(θ − θ_crit)

    Cardioid coupling (optional, mathematical layer):
        envelope = 1 + cardioid_amp · cos(θ)
        non-diffusive RHS is multiplied by envelope:
        ∂t θ = D ∇²θ + envelope · (cot_term + δω − κ⟨θ⟩ + burst)

    At the cusp θ≈π, cos(θ)≈−1 so envelope ≈ 1 − cardioid_amp (suppressed
    drive when amp>0); at θ≈0, envelope ≈ 1 + cardioid_amp (enhanced).
    This is a directional resonance envelope on the existing dynamics — not
    a claim that the cardioid is forced by the Hopf lattice.
    """
    if normalize_to_lambda_t is not None:
        nt = max(1, int(round(normalize_to_lambda_t / (kappa * dt))))
    if theta_crit is None:
        theta_crit = PI * (1 + kappa)
    if initial_theta is not None:
        theta = initial_theta.copy()
    else:
        rng = np.random.default_rng(seed)
        theta = rng.uniform(0.1, 2.0, (nx, nx, nx))

    for _ in range(nt):
        lap = (
            np.roll(theta, 1, 0) + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1) + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2) + np.roll(theta, -1, 2) - 6 * theta
        ) / (1.0 / nx) ** 2
        with np.errstate(divide="ignore", invalid="ignore"):
            cot_term = (
                (D / 2.0) * np.cos(theta / 2.0) / np.sin(theta / 2.0)
                * (
                    np.gradient(theta, axis=0) ** 2
                    + np.gradient(theta, axis=1) ** 2
                    + np.gradient(theta, axis=2) ** 2
                ).sum(axis=0)
            )
        gauge = -kappa * theta.mean()
        burst = np.where(theta > theta_crit, -50.0 * (theta - theta_crit), 0.0)
        # Non-diffusive drive (optionally cardioid-modulated)
        drive = cot_term + delta_omega + gauge + burst
        if cardioid_amp != 0.0:
            # envelope = 1 + A cos(θ)  — same cardioid family as geometric probes
            envelope = 1.0 + cardioid_amp * np.cos(theta)
            drive = envelope * drive
        theta += dt * (D * lap + drive)
        theta = np.clip(theta, 0.01, 2 * PI - 0.01)
    return theta


def fft_analysis(theta: np.ndarray) -> dict:
    """Dominant k-modes on middle z-slice."""
    sl = theta[:, :, theta.shape[2] // 2]
    sl = sl - sl.mean()
    fft = np.fft.fft2(sl)
    power = np.abs(fft) ** 2
    ky, kx = np.unravel_index(np.argsort(power.ravel())[::-1][:8], power.shape)
    modes = []
    for i in range(8):
        modes.append({
            "kx": int(kx[i]),
            "ky": int(ky[i]),
            "power_frac": float(power[ky[i], kx[i]] / power.sum()),
        })
    return {"top_modes": modes, "total_power": float(power.sum())}


def correlation_length(theta: np.ndarray) -> dict:
    sl = theta[:, :, theta.shape[2] // 2]
    sl = sl - sl.mean()
    fft = np.fft.fft2(sl)
    power = np.abs(fft) ** 2
    nx = sl.shape[0]
    kx = np.fft.fftfreq(nx) * nx
    ky = np.fft.fftfreq(nx) * nx
    KX, KY = np.meshgrid(kx, ky)
    k_mag = np.sqrt(KX**2 + KY**2)
    k_mag[0, 0] = 1e-12
    mean_k = float((power * k_mag).sum() / power.sum())
    xi = float(nx / mean_k) if mean_k > 0 else float(nx)
    return {"mean_k": mean_k, "correlation_length_grid_units": xi}


def ratio_signature(values: dict[str, float], field_std: float, nx: int) -> dict:
    """Compare emergent length scales to φ, e, π ratios."""
    xi = values.get("correlation_length_grid_units", 1.0)
    mean_k = values.get("mean_k", 1.0)
    degenerate = field_std < 1e-6 or mean_k < 1e-6

    candidates = {
        "xi_over_nx": xi / nx,
        "mean_k_over_pi": mean_k / PI,
        "mean_k_over_phi": mean_k / PHI,
        "mean_k_over_e": mean_k / E,
    }
    nearest = []
    if not degenerate:
        for name, val in candidates.items():
            best = min(TRANSCENDENTALS.items(), key=lambda kv: abs(val - kv[1]))
            nearest.append({
                "ratio": name,
                "value": val,
                "nearest_transcendental": best[0],
                "delta_pct": 100 * abs(val - best[1]) / abs(best[1]),
            })
        nearest.sort(key=lambda x: x["delta_pct"])

    return {
        "candidates": candidates,
        "nearest_ranking": nearest[:5],
        "degenerate_uniform_field": degenerate,
        "note": (
            "Uniform relaxed field: ξ→grid size, mean_k→0. No meaningful φ/e/π FFT signature."
            if degenerate
            else "Non-uniform structure present; ratios may be informative."
        ),
    }


def cusp_field_metrics(theta: np.ndarray, half_width: float = CUSP_W) -> dict:
    """
    Fraction of lattice sites in the cardioid cusp angular window |θ − π| ≤ w,
    plus radial-style collapse using θ as the field value itself.
    """
    d = np.abs(((theta - PI + PI) % (2.0 * PI)) - PI)
    near = d <= half_width
    frac = float(np.mean(near))
    expected = (2.0 * half_width) / (2.0 * PI)
    mean_cusp = float(np.mean(theta[near])) if near.any() else float("nan")
    mean_bulk = float(np.mean(theta[~near])) if (~near).any() else float("nan")
    # For PDE fields θ itself plays the role of the polar radius proxy
    collapse = (
        mean_bulk / (mean_cusp + 1e-12) if mean_cusp == mean_cusp and near.any() else float("nan")
    )
    return {
        "cusp_site_fraction": frac,
        "expected_uniform_fraction": float(expected),
        "cusp_density_ratio": float(frac / expected) if expected > 0 else float("nan"),
        "mean_theta_cusp": mean_cusp,
        "mean_theta_bulk": mean_bulk,
        "radial_collapse_proxy": float(collapse) if collapse == collapse else float("nan"),
        "n_cusp_sites": int(np.sum(near)),
        "vortex_369_all": digital_root_bin(theta),
        "vortex_369_cusp": digital_root_bin(theta[near]) if near.any() else {
            "counts": {}, "fraction_369": 0.0, "n": 0,
        },
    }


def phi_e_pi_field_align_support(theta: np.ndarray, sigma: float = 0.20) -> dict:
    """
    Field analogue of geometric align_support: Gaussian-weighted mean of
    (θ / (2π)) near the triangle angles (≈31°, 59.9°, 89.1°).
    """
    targets = np.radians([30.996, 59.900, 89.104])
    supports = []
    for alpha in targets:
        d = np.abs(((theta - alpha + PI) % (2.0 * PI)) - PI)
        w = np.exp(-0.5 * (d / sigma) ** 2)
        if w.sum() < 1e-12:
            supports.append(0.0)
        else:
            supports.append(float(np.average(theta / (2.0 * PI), weights=w)))
    return {
        "align_support": float(np.mean(supports)),
        "per_angle": {
            "phi": supports[0],
            "e": supports[1],
            "pi": supports[2],
        },
        "formula": "mean_α[(Σ w θ/(2π))/(Σ w)], w=exp(−½ dist(θ,α)²/σ²)",
    }


def plot_slice(theta: np.ndarray, path: Path, *, title_suffix: str = "") -> None:
    sl = theta[:, :, theta.shape[2] // 2]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    im = axes[0].imshow(sl, cmap="twilight", origin="lower")
    axes[0].set_title(f"Relaxed θ(x,y) mid-slice{title_suffix}")
    plt.colorbar(im, ax=axes[0], fraction=0.046)
    power = np.abs(np.fft.fftshift(np.fft.fft2(sl - sl.mean()))) ** 2
    axes[1].imshow(np.log1p(power), cmap="magma", origin="lower")
    axes[1].set_title("log FFT power")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cardioid_compare(
    theta_raw: np.ndarray,
    theta_mod: np.ndarray,
    path: Path,
    *,
    cardioid_amp: float,
    ic_name: str = "uniform",
) -> None:
    """Side-by-side mid-slice + histogram: baseline PDE vs cardioid-modulated."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    # Adaptive color scale for structured ICs that retain variance
    vmax = max(float(theta_raw.max()), float(theta_mod.max()), 0.5)
    for ax, th, label in (
        (axes[0, 0], theta_raw, "baseline"),
        (axes[0, 1], theta_mod, f"cardioid A={cardioid_amp}"),
    ):
        sl = th[:, :, th.shape[2] // 2]
        im = ax.imshow(sl, cmap="twilight", origin="lower", vmin=0, vmax=vmax)
        ax.set_title(f"θ mid-slice — {label}\nσ={float(th.std()):.4f}")
        plt.colorbar(im, ax=ax, fraction=0.046)

    axes[1, 0].hist(theta_raw.ravel(), bins=40, color="#457b9d", alpha=0.75, density=True, label="baseline")
    axes[1, 0].hist(theta_mod.ravel(), bins=40, color="#e63946", alpha=0.55, density=True, label="cardioid")
    axes[1, 0].axvline(PI, color="#333", ls="--", lw=0.9, label="θ=π cusp")
    t_crit = PI * (1 + 0.85)
    axes[1, 0].axvline(t_crit, color="#c9a227", ls=":", lw=1.0, label="θ_crit≈π(1+κ)")
    axes[1, 0].set_xlabel("θ")
    axes[1, 0].set_ylabel("density")
    axes[1, 0].set_title("Field histogram")
    axes[1, 0].legend(fontsize=7)
    axes[1, 0].grid(alpha=0.3)

    m_raw = cusp_field_metrics(theta_raw)
    m_mod = cusp_field_metrics(theta_mod)
    a_raw = phi_e_pi_field_align_support(theta_raw)
    a_mod = phi_e_pi_field_align_support(theta_mod)
    ax = axes[1, 1]
    labels = ["cusp_frac", "align", "frac369", "σ"]
    raw_vals = [
        m_raw["cusp_site_fraction"],
        a_raw["align_support"],
        m_raw["vortex_369_all"]["fraction_369"],
        float(theta_raw.std()),
    ]
    mod_vals = [
        m_mod["cusp_site_fraction"],
        a_mod["align_support"],
        m_mod["vortex_369_all"]["fraction_369"],
        float(theta_mod.std()),
    ]
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w / 2, raw_vals, w, color="#457b9d", label="baseline")
    ax.bar(x + w / 2, mod_vals, w, color="#e63946", label="cardioid")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("Cusp / align / 369 / σ")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3, axis="y")

    fig.suptitle(
        f"PDE cardioid compare · IC={ic_name} · A={cardioid_amp}\n"
        "envelope = 1 + A·cos(θ) on non-diffusive drive",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def survival_at_lambda_t(
    theta: np.ndarray,
    theta0_mean: float,
    theta0_std: float,
) -> dict:
    """Survival fractions vs e^{-2} and R after normalized relaxation."""
    e_inv2 = float(np.exp(-2.0))
    r_residual = PHI**2 + E**2 - PI**2
    mean_surv = float(theta.mean() / theta0_mean) if abs(theta0_mean) > 1e-12 else 0.0
    std_surv = float(theta.std() / theta0_std) if theta0_std > 1e-12 else 0.0
    return {
        "mean_survival": mean_surv,
        "std_survival": std_surv,
        "e_inv2": e_inv2,
        "R_residual": r_residual,
        "delta_pct_vs_e_inv2": 100 * abs(mean_surv - e_inv2) / e_inv2,
        "delta_pct_vs_R": 100 * abs(mean_surv - r_residual) / abs(r_residual),
    }


def _package_field(theta: np.ndarray, theta0_mean: float, theta0_std: float, normalize_lt) -> dict:
    fft = fft_analysis(theta)
    corr = correlation_length(theta)
    sig = ratio_signature(corr, float(theta.std()), theta.shape[0])
    survival = (
        survival_at_lambda_t(theta, theta0_mean, theta0_std) if normalize_lt else None
    )
    cusp = cusp_field_metrics(theta)
    align = phi_e_pi_field_align_support(theta)
    return {
        "field_stats": {
            "mean": float(theta.mean()),
            "std": float(theta.std()),
            "min": float(theta.min()),
            "max": float(theta.max()),
        },
        "fft": fft,
        "correlation": corr,
        "phi_e_pi_signature": sig,
        "lambda_t_survival": survival,
        "cusp_field": cusp,
        "align_support": align,
        "vortex_369_fraction": cusp["vortex_369_all"]["fraction_369"],
        "vortex_369_cusp_fraction": cusp["vortex_369_cusp"]["fraction_369"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PDE relaxation probe (+ optional cardioid)")
    parser.add_argument(
        "--cardioid-amp",
        type=float,
        default=None,
        help="Cardioid envelope amplitude A on non-diffusive drive (default: env CARDIOID_AMP or 0)",
    )
    parser.add_argument(
        "--compare-cardioid",
        action="store_true",
        help="Run baseline + cardioid side-by-side (uses --cardioid-amp or 0.5)",
    )
    parser.add_argument(
        "--ic",
        choices=("uniform", "hopfion", "helical", "combined"),
        default="uniform",
        help="Initial condition (structured ICs retain σ under relaxation)",
    )
    parser.add_argument("--nx", type=int, default=20)
    parser.add_argument("--nt", type=int, default=3000)
    args = parser.parse_args()

    seeds = load_meta_seeds()
    kappa = seeds["kappa"]
    theta_crit = PI * (1 + kappa)
    normalize_lt = float(os.environ.get("NORMALIZE_TO_LAMBDA_T", "0")) or None
    if normalize_lt is not None and normalize_lt <= 0:
        normalize_lt = None

    env_amp = float(os.environ.get("CARDIOID_AMP", "0") or 0)
    cardioid_amp = args.cardioid_amp if args.cardioid_amp is not None else env_amp
    compare = args.compare_cardioid or os.environ.get("COMPARE_CARDIOID", "") == "1"
    if compare and cardioid_amp == 0.0:
        cardioid_amp = 0.5

    print(f"PDE seeds: κ={kappa}, θ_crit={theta_crit:.4f}, W_g={seeds['w_g']:.4f}")
    if normalize_lt:
        print(f"Normalizing to λt = {normalize_lt} (λ ≈ κ)")
    print(f"IC={args.ic}  cardioid_amp={cardioid_amp}  compare={compare}")

    theta0 = build_ic(args.ic, args.nx, seed=42, kappa=kappa)
    theta0_mean, theta0_std = float(theta0.mean()), float(theta0.std())
    ic_cusp = cusp_field_metrics(theta0)
    ic_align = phi_e_pi_field_align_support(theta0)
    print(
        f"IC stats: ⟨θ₀⟩={theta0_mean:.4f}  σ₀={theta0_std:.4f}  "
        f"cusp₀={ic_cusp['cusp_site_fraction']:.4f}  "
        f"369₀={ic_cusp['vortex_369_all']['fraction_369']:.3f}  "
        f"align₀={ic_align['align_support']:.4f}"
    )
    # Structured ICs: default early-time window retains finite-k structure
    # (full nt=3000 still dissipates — see pde_structured_ic_probe)
    if args.ic != "uniform" and args.nt == 3000 and "NORMALIZE_TO_LAMBDA_T" not in os.environ:
        args.nt = 400
        print(f"Structured IC: using early-time window nt={args.nt} (override with --nt)")

    theta_raw = simulate_pde(
        nx=args.nx,
        nt=args.nt,
        kappa=kappa,
        theta_crit=theta_crit,
        normalize_to_lambda_t=normalize_lt,
        cardioid_amp=0.0,
        initial_theta=theta0,
    )
    pkg_raw = _package_field(theta_raw, theta0_mean, theta0_std, normalize_lt)

    theta_mod = None
    pkg_mod = None
    if compare or cardioid_amp != 0.0:
        amp_run = cardioid_amp if cardioid_amp != 0.0 else 0.5
        theta_mod = simulate_pde(
            nx=args.nx,
            nt=args.nt,
            kappa=kappa,
            theta_crit=theta_crit,
            normalize_to_lambda_t=normalize_lt,
            cardioid_amp=amp_run,
            initial_theta=theta0,
        )
        pkg_mod = _package_field(theta_mod, theta0_mean, theta0_std, normalize_lt)
        cardioid_amp = amp_run

    # Primary field for legacy single plot: modulated if requested, else baseline
    theta = theta_mod if (cardioid_amp != 0.0 and theta_mod is not None and not compare) else theta_raw
    pkg = pkg_mod if (cardioid_amp != 0.0 and pkg_mod is not None and not compare) else pkg_raw

    plot_path = OUTPUT_DIR / "pde_relaxation_probe.png"
    if args.ic != "uniform":
        plot_path = OUTPUT_DIR / f"pde_relaxation_probe_{args.ic}.png"
    suffix = f"  A={cardioid_amp}" if cardioid_amp and not compare else ""
    suffix = f"  IC={args.ic}{suffix}"
    plot_slice(theta, plot_path, title_suffix=suffix)

    compare_path = None
    if compare and theta_mod is not None:
        tag = "" if args.ic == "uniform" else f"_{args.ic}"
        compare_path = OUTPUT_DIR / f"pde_cardioid_compare{tag}.png"
        plot_cardioid_compare(
            theta_raw, theta_mod, compare_path,
            cardioid_amp=cardioid_amp, ic_name=args.ic,
        )

    result = {
        "meta_seeds": seeds,
        "ic": args.ic,
        "normalize_to_lambda_t": normalize_lt,
        "theta_crit_rad": theta_crit,
        "cardioid_amp": cardioid_amp,
        "cardioid_formula": (
            "drive ← (1 + A·cos(θ)) · (cot + δω + gauge + burst); "
            "diffusion unmodulated"
        ),
        "ic_stats": {
            "mean": theta0_mean,
            "std": theta0_std,
            "cusp_field": ic_cusp,
            "align_support": ic_align,
        },
        "nt": args.nt,
        "baseline": pkg_raw,
        "cardioid": pkg_mod,
        "field_stats": pkg["field_stats"],
        "fft": pkg["fft"],
        "correlation": pkg["correlation"],
        "phi_e_pi_signature": pkg["phi_e_pi_signature"],
        "lambda_t_survival": pkg.get("lambda_t_survival"),
        "align_support": pkg.get("align_support"),
        "vortex_369_fraction": pkg.get("vortex_369_fraction"),
        "plot": str(plot_path),
        "compare_plot": str(compare_path) if compare_path else None,
        "interpretation": pkg["phi_e_pi_signature"]["note"],
    }
    if compare and pkg_mod is not None:
        result["cardioid_delta"] = {
            "mean_theta": pkg_mod["field_stats"]["mean"] - pkg_raw["field_stats"]["mean"],
            "std_theta": pkg_mod["field_stats"]["std"] - pkg_raw["field_stats"]["std"],
            "cusp_frac_delta": (
                pkg_mod["cusp_field"]["cusp_site_fraction"]
                - pkg_raw["cusp_field"]["cusp_site_fraction"]
            ),
            "cusp_rho_delta": (
                pkg_mod["cusp_field"]["cusp_density_ratio"]
                - pkg_raw["cusp_field"]["cusp_density_ratio"]
            ),
            "align_support_delta": (
                pkg_mod["align_support"]["align_support"]
                - pkg_raw["align_support"]["align_support"]
            ),
            "vortex_369_delta": (
                pkg_mod["vortex_369_fraction"] - pkg_raw["vortex_369_fraction"]
            ),
            "vortex_369_cusp_delta": (
                pkg_mod["vortex_369_cusp_fraction"] - pkg_raw["vortex_369_cusp_fraction"]
            ),
            "R_residual": float(R_RESIDUAL),
        }

    report_path = save_report("pde_relaxation_probe", result)

    print("=== PDE Relaxation Probe ===")
    print(f"IC={args.ic}  ⟨θ⟩={result['field_stats']['mean']:.4f}  σ={result['field_stats']['std']:.4f}")
    print(f"Correlation length ξ={pkg['correlation']['correlation_length_grid_units']:.3f} grid units")
    if compare and pkg_mod is not None:
        d = result["cardioid_delta"]
        print(
            f"Cardioid compare A={cardioid_amp}: "
            f"⟨θ⟩ {pkg_raw['field_stats']['mean']:.4f}→{pkg_mod['field_stats']['mean']:.4f}  "
            f"σ {pkg_raw['field_stats']['std']:.4f}→{pkg_mod['field_stats']['std']:.4f}"
        )
        print(
            f"  cusp_frac {pkg_raw['cusp_field']['cusp_site_fraction']:.4f}"
            f"→{pkg_mod['cusp_field']['cusp_site_fraction']:.4f}  "
            f"align {pkg_raw['align_support']['align_support']:.4f}"
            f"→{pkg_mod['align_support']['align_support']:.4f}  "
            f"369 {pkg_raw['vortex_369_fraction']:.3f}"
            f"→{pkg_mod['vortex_369_fraction']:.3f}  "
            f"(Δalign={d['align_support_delta']:+.4f}, Δ369={d['vortex_369_delta']:+.4f})"
        )
    surv = pkg.get("lambda_t_survival")
    if surv:
        print(f"λt survival: mean={surv['mean_survival']:.6f}  "
              f"(e^{{-2}}={surv['e_inv2']:.6f}, R={surv['R_residual']:.6f})")
        print(f"  Δ vs e^{{-2}}: {surv['delta_pct_vs_e_inv2']:.2f}%  "
              f"Δ vs R: {surv['delta_pct_vs_R']:.2f}%")
    if pkg["phi_e_pi_signature"].get("degenerate_uniform_field"):
        print("Field uniform after relaxation — no meaningful φ/e/π length-scale signature.")
    else:
        top = pkg["phi_e_pi_signature"]["nearest_ranking"][0]
        print(f"Best ratio match: {top['ratio']}={top['value']:.4f} → {top['nearest_transcendental']} "
              f"(Δ {top['delta_pct']:.1f}%)")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    if compare_path:
        print(f"Compare:{compare_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
