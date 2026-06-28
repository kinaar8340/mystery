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
) -> np.ndarray:
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


def main() -> int:
    seeds = load_meta_seeds()
    kappa = seeds["kappa"]
    theta_crit = PI * (1 + kappa)

    print(f"PDE seeds: κ={kappa}, θ_crit={theta_crit:.4f}, W_g={seeds['w_g']:.4f}")
    theta = simulate_pde(kappa=kappa, theta_crit=theta_crit)

    fft = fft_analysis(theta)
    corr = correlation_length(theta)
    sig = ratio_signature(corr, float(theta.std()), theta.shape[0])
    plot_path = OUTPUT_DIR / "pde_relaxation_probe.png"
    plot_slice(theta, plot_path)

    result = {
        "meta_seeds": seeds,
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