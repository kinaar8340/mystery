#!/usr/bin/env python3
"""PDE relaxation seeded with meta-optimizer constants; FFT + correlation analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

META_JSON = OUTPUT_DIR / "meta_optimize_phi_probe_20260628_022307.json"
TRANSCENDENTALS = {"phi": PHI, "e": E, "pi": PI, "one": 1.0}


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
) -> np.ndarray:
    # When normalize_to_lambda_t is set, evolve to λt = target with λ ≈ κ (gauge rate).
    if normalize_to_lambda_t is not None:
        nt = max(1, int(round(normalize_to_lambda_t / (kappa * dt))))
    if theta_crit is None:
        theta_crit = PI * (1 + kappa)
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
                * (np.gradient(theta, axis=0) ** 2 + np.gradient(theta, axis=1) ** 2 + np.gradient(theta, axis=2) ** 2).sum(axis=0)
            )
        gauge = -kappa * theta.mean()
        burst = np.where(theta > theta_crit, -50.0 * (theta - theta_crit), 0.0)
        theta += dt * (D * lap + cot_term + delta_omega + gauge + burst)
        theta = np.clip(theta, 0.01, 2 * PI - 0.01)
    return theta


def fft_analysis(theta: np.ndarray) -> dict:
    """Dominant k-modes on middle z-slice."""
    sl = theta[:, :, theta.shape[2] // 2]
    sl = sl - sl.mean()
    fft = np.fft.fft2(sl)
    power = np.abs(fft) ** 2
    ky, kx = np.unravel_index(np.argsort(power.ravel())[::-1][:8], power.shape)
    nx = sl.shape[0]
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


def plot_slice(theta: np.ndarray, path: Path) -> None:
    sl = theta[:, :, theta.shape[2] // 2]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    im = axes[0].imshow(sl, cmap="twilight", origin="lower")
    axes[0].set_title("Relaxed θ(x,y) mid-slice")
    plt.colorbar(im, ax=axes[0], fraction=0.046)
    power = np.abs(np.fft.fftshift(np.fft.fft2(sl - sl.mean()))) ** 2
    axes[1].imshow(np.log1p(power), cmap="magma", origin="lower")
    axes[1].set_title("log FFT power")
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


def main() -> int:
    import os

    seeds = load_meta_seeds()
    kappa = seeds["kappa"]
    theta_crit = PI * (1 + kappa)
    normalize_lt = float(os.environ.get("NORMALIZE_TO_LAMBDA_T", "0")) or None
    if normalize_lt is not None and normalize_lt <= 0:
        normalize_lt = None

    print(f"PDE seeds: κ={kappa}, θ_crit={theta_crit:.4f}, W_g={seeds['w_g']:.4f}")
    if normalize_lt:
        print(f"Normalizing to λt = {normalize_lt} (λ ≈ κ)")
    rng = np.random.default_rng(42)
    theta0 = rng.uniform(0.1, 2.0, (20, 20, 20))
    theta0_mean, theta0_std = float(theta0.mean()), float(theta0.std())
    theta = simulate_pde(
        kappa=kappa,
        theta_crit=theta_crit,
        normalize_to_lambda_t=normalize_lt,
    )

    fft = fft_analysis(theta)
    corr = correlation_length(theta)
    sig = ratio_signature(corr, float(theta.std()), theta.shape[0])
    plot_path = OUTPUT_DIR / "pde_relaxation_probe.png"
    plot_slice(theta, plot_path)

    survival = (
        survival_at_lambda_t(theta, theta0_mean, theta0_std) if normalize_lt else None
    )

    result = {
        "meta_seeds": seeds,
        "normalize_to_lambda_t": normalize_lt,
        "lambda_t_survival": survival,
        "theta_crit_rad": theta_crit,
        "field_stats": {
            "mean": float(theta.mean()),
            "std": float(theta.std()),
            "min": float(theta.min()),
            "max": float(theta.max()),
        },
        "fft": fft,
        "correlation": corr,
        "phi_e_pi_signature": sig,
        "plot": str(plot_path),
        "interpretation": sig["note"],
    }
    report_path = save_report("pde_relaxation_probe", result)

    print("=== PDE Relaxation Probe ===")
    print(f"⟨θ⟩={result['field_stats']['mean']:.4f}  σ={result['field_stats']['std']:.4f}")
    print(f"Correlation length ξ={corr['correlation_length_grid_units']:.3f} grid units")
    if survival:
        print(f"λt survival: mean={survival['mean_survival']:.6f}  "
              f"(e^{{-2}}={survival['e_inv2']:.6f}, R={survival['R_residual']:.6f})")
        print(f"  Δ vs e^{{-2}}: {survival['delta_pct_vs_e_inv2']:.2f}%  "
              f"Δ vs R: {survival['delta_pct_vs_R']:.2f}%")
    if sig.get("degenerate_uniform_field"):
        print("Field uniform after relaxation — no meaningful φ/e/π length-scale signature.")
    else:
        top = sig["nearest_ranking"][0]
        print(f"Best ratio match: {top['ratio']}={top['value']:.4f} → {top['nearest_transcendental']} "
              f"(Δ {top['delta_pct']:.1f}%)")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())